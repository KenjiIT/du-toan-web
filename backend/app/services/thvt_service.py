# -*- coding: utf-8 -*-
"""Tổng hợp vật tư (THVT) — Material/Labor/Machine Summary service."""

from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.don_gia import DonGia, PhuLucVua
from app.models.project import Project, ProjectItem, ProjectSettings
from app.services.price_calculator import (
    MORTAR_PLACEHOLDER_CODES,
    _get_first_resource_group,
    _get_resource_price,
    _resolve_mortar,
)


def calculate_thvt(db: Session, project_id: int) -> dict:
    """Aggregate all resources across all project items.

    Returns dict with keys: vat_lieu, nhan_cong, may_thi_cong,
    total_vl, total_nc, total_mtc, total, item_count, resource_count.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return {"error": "Project not found"}

    settings = (
        db.query(ProjectSettings)
        .filter(ProjectSettings.project_id == project_id)
        .first()
    )
    reg = settings.regulation_code if settings else "TT12-2021"
    dbt = settings.db_type if settings else "XD+LD+SC"
    src = settings.source if settings else "norm"

    items = db.query(ProjectItem).filter(ProjectItem.project_id == project_id).all()

    # msvt -> {total_hao_phi, tvt, dvt}
    agg: dict[str, dict] = defaultdict(lambda: {"total_hao_phi": 0.0, "tvt": None, "dvt": None, "gia": 0.0})

    item_count = 0

    for item in items:
        qty = item.quantity or 0
        if qty == 0:
            continue

        # Find don_gia to get mhdm and plv
        dg = (
            db.query(DonGia)
            .filter(
                DonGia.mhdg == item.mhdg,
                DonGia.regulation_code == reg,
                DonGia.db_type == dbt,
            )
            .first()
        )
        if not dg:
            dg = (
                db.query(DonGia)
                .filter(
                    DonGia.mhdg == item.mhdg,
                    DonGia.regulation_code == reg,
                )
                .first()
            )
        if not dg or not dg.mhdm:
            continue

        item_count += 1
        dm_rows = _get_first_resource_group(db, dg.mhdm, reg, dbt)

        # Resolve mortar recipe if present
        plv_info = None
        mortar_cost = 0.0
        if dg.plv:
            plv_info = _resolve_mortar(db, dg.plv, reg, dbt, src)
            if plv_info:
                mortar_cost = plv_info["total_cost"]

        all_codes = {dm.msvt for dm in dm_rows}
        has_v19999 = "V19999" in all_codes

        for dm in dm_rows:
            if not dm.msvt:
                continue
            hp = dm.hao_phi or 0
            if hp == 0:
                continue

            is_mortar = dm.msvt in MORTAR_PLACEHOLDER_CODES and mortar_cost > 0
            if dm.msvt == "V10875" and has_v19999:
                is_mortar = False

            if is_mortar:
                # Expand mortar recipe: add each component individually
                if plv_info:
                    for comp in plv_info["components"]:
                        comp_msvt = comp["msvt"]
                        comp_hp = comp["hao_phi"] or 0
                        # mortar placeholder hao_phi * component hao_phi * item qty
                        total_hp = hp * comp_hp * qty
                        entry = agg[comp_msvt]
                        entry["total_hao_phi"] += total_hp
                        if entry["tvt"] is None:
                            entry["tvt"] = comp["tvt"]
                            entry["dvt"] = comp["dvt"]
                            entry["gia"] = comp["gia"]
                continue

            if dm.msvt in MORTAR_PLACEHOLDER_CODES:
                continue

            price, name, dvt = _get_resource_price(db, dm.msvt, reg, dbt, src)

            total_hp = hp * qty
            entry = agg[dm.msvt]
            entry["total_hao_phi"] += total_hp
            if entry["tvt"] is None:
                entry["tvt"] = name
                entry["dvt"] = dvt
                entry["gia"] = price

    # Build categorized lists
    vat_lieu = []
    nhan_cong = []
    may_thi_cong = []

    for msvt, info in agg.items():
        gia = info["gia"] or 0
        total_hp = info["total_hao_phi"]
        thanh_tien = round(total_hp * gia)
        row = {
            "msvt": msvt,
            "tvt": info["tvt"],
            "dvt": info["dvt"],
            "total_hao_phi": round(total_hp, 4),
            "gia": round(gia),
            "thanh_tien": thanh_tien,
        }
        if msvt.startswith("V"):
            vat_lieu.append(row)
        elif msvt.startswith("N"):
            nhan_cong.append(row)
        elif msvt.startswith("M"):
            may_thi_cong.append(row)
        else:
            vat_lieu.append(row)

    # Sort each category by msvt
    vat_lieu.sort(key=lambda r: r["msvt"])
    nhan_cong.sort(key=lambda r: r["msvt"])
    may_thi_cong.sort(key=lambda r: r["msvt"])

    total_vl = sum(r["thanh_tien"] for r in vat_lieu)
    total_nc = sum(r["thanh_tien"] for r in nhan_cong)
    total_mtc = sum(r["thanh_tien"] for r in may_thi_cong)

    return {
        "vat_lieu": vat_lieu,
        "nhan_cong": nhan_cong,
        "may_thi_cong": may_thi_cong,
        "total_vl": total_vl,
        "total_nc": total_nc,
        "total_mtc": total_mtc,
        "total": total_vl + total_nc + total_mtc,
        "item_count": item_count,
        "resource_count": {
            "vl": len(vat_lieu),
            "nc": len(nhan_cong),
            "mtc": len(may_thi_cong),
        },
    }


def generate_thvt_excel(project_name: str, thvt_data: dict):
    """Generate an Excel workbook with 3 sheets for THVT."""
    import io
    from datetime import datetime

    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

    wb = Workbook()

    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )
    header_font = Font(bold=True, size=11)
    title_font = Font(bold=True, size=14)
    header_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    number_format = "#,##0"
    hp_format = "#,##0.0000"

    categories = [
        ("Vật liệu", thvt_data["vat_lieu"], thvt_data["total_vl"]),
        ("Nhân công", thvt_data["nhan_cong"], thvt_data["total_nc"]),
        ("Máy thi công", thvt_data["may_thi_cong"], thvt_data["total_mtc"]),
    ]

    for idx, (sheet_name, resources, total) in enumerate(categories):
        if idx == 0:
            ws = wb.active
            ws.title = sheet_name
        else:
            ws = wb.create_sheet(sheet_name)

        # Title
        ws.merge_cells("A1:G1")
        cell = ws["A1"]
        cell.value = f"TỔNG HỢP VẬT TƯ - {sheet_name.upper()}"
        cell.font = title_font
        cell.alignment = Alignment(horizontal="center")

        ws.merge_cells("A2:G2")
        cell = ws["A2"]
        cell.value = f"Công trình: {project_name}"
        cell.font = Font(bold=True, size=12)
        cell.alignment = Alignment(horizontal="center")

        # Column headers
        headers = [
            ("STT", 6),
            ("Mã vật tư", 16),
            ("Tên vật tư", 45),
            ("ĐVT", 10),
            ("Tổng hao phí", 16),
            ("Đơn giá", 16),
            ("Thành tiền", 20),
        ]

        header_row = 4
        for col_idx, (header_text, width) in enumerate(headers, 1):
            cell = ws.cell(row=header_row, column=col_idx, value=header_text)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center", wrap_text=True)
            from openpyxl.utils import get_column_letter
            ws.column_dimensions[get_column_letter(col_idx)].width = width

        # Data rows
        for row_idx, res in enumerate(resources, header_row + 1):
            stt = row_idx - header_row
            values = [
                stt,
                res["msvt"],
                res["tvt"] or "",
                res["dvt"] or "",
                res["total_hao_phi"],
                res["gia"],
                res["thanh_tien"],
            ]
            for col_idx, val in enumerate(values, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.border = thin_border
                if col_idx == 5:
                    cell.number_format = hp_format
                    cell.alignment = Alignment(horizontal="right")
                elif col_idx >= 6:
                    cell.number_format = number_format
                    cell.alignment = Alignment(horizontal="right")
                elif col_idx == 1:
                    cell.alignment = Alignment(horizontal="center")

        # Totals row
        if resources:
            total_row = header_row + len(resources) + 1
            ws.merge_cells(f"A{total_row}:F{total_row}")
            cell = ws.cell(row=total_row, column=1, value="TỔNG CỘNG")
            cell.font = header_font
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center")
            for col_idx in range(2, 7):
                ws.cell(row=total_row, column=col_idx).border = thin_border

            cell = ws.cell(row=total_row, column=7, value=total)
            cell.font = header_font
            cell.border = thin_border
            cell.number_format = number_format
            cell.alignment = Alignment(horizontal="right")

            # Footer
            footer_row = total_row + 2
            ws.cell(
                row=footer_row, column=7,
                value=f"Ngày xuất: {datetime.now().strftime('%d/%m/%Y')}",
            )

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
