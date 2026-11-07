# -*- coding: utf-8 -*-
"""Service for bid package (goi thau) management."""

import io
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from app.models.project import BidPackage, ProjectItem, ProjectSettings
from app.services.cost_summary import calculate_section_summary


def _item_to_response(item: ProjectItem) -> dict:
    """Convert a ProjectItem ORM object to a response dict."""
    qty = item.quantity or 0
    eff_vlc = item.override_vlc if item.override_vlc is not None else (item.vlc or 0)
    eff_nc = item.override_nc if item.override_nc is not None else (item.nc or 0)
    eff_mtc = item.override_mtc if item.override_mtc is not None else (item.mtc or 0)
    return {
        "id": item.id,
        "mhdg": item.mhdg,
        "tcv": item.tcv,
        "dvt": item.dvt,
        "quantity": qty,
        "vlc": item.vlc or 0,
        "vlp": item.vlp or 0,
        "nc": item.nc or 0,
        "mtc": item.mtc or 0,
        "override_vlc": item.override_vlc,
        "override_nc": item.override_nc,
        "override_mtc": item.override_mtc,
        "notes": item.notes,
        "sort_order": item.sort_order or 0,
        "section_id": item.section_id,
        "thanh_tien_vlc": round(qty * eff_vlc),
        "thanh_tien_nc": round(qty * eff_nc),
        "thanh_tien_mtc": round(qty * eff_mtc),
        "thanh_tien": round(qty * (eff_vlc + eff_nc + eff_mtc)),
    }


def get_bid_packages(db: Session, project_id: int) -> list[dict]:
    """List all bid packages for a project with item counts and cost totals."""
    packages = (
        db.query(BidPackage)
        .filter(BidPackage.project_id == project_id)
        .order_by(BidPackage.sort_order, BidPackage.id)
        .all()
    )

    result = []
    for pkg in packages:
        items = (
            db.query(ProjectItem)
            .filter(ProjectItem.bid_package_id == pkg.id)
            .all()
        )
        total_vlc = 0.0
        total_nc = 0.0
        total_mtc = 0.0
        for item in items:
            qty = item.quantity or 0
            eff_vlc = item.override_vlc if item.override_vlc is not None else (item.vlc or 0)
            eff_nc = item.override_nc if item.override_nc is not None else (item.nc or 0)
            eff_mtc = item.override_mtc if item.override_mtc is not None else (item.mtc or 0)
            total_vlc += qty * eff_vlc
            total_nc += qty * eff_nc
            total_mtc += qty * eff_mtc

        result.append({
            "id": pkg.id,
            "project_id": pkg.project_id,
            "name": pkg.name,
            "package_type": pkg.package_type,
            "description": pkg.description,
            "sort_order": pkg.sort_order or 0,
            "created_at": pkg.created_at,
            "updated_at": pkg.updated_at,
            "item_count": len(items),
            "total_cost": round(total_vlc + total_nc + total_mtc),
            "vlc": round(total_vlc),
            "nc": round(total_nc),
            "mtc": round(total_mtc),
        })

    return result


def get_bid_package_detail(db: Session, package_id: int) -> dict | None:
    """Get a bid package with items and cost breakdown."""
    pkg = db.query(BidPackage).filter(BidPackage.id == package_id).first()
    if not pkg:
        return None

    items = (
        db.query(ProjectItem)
        .filter(ProjectItem.bid_package_id == pkg.id)
        .order_by(ProjectItem.sort_order)
        .all()
    )

    settings = (
        db.query(ProjectSettings)
        .filter(ProjectSettings.project_id == pkg.project_id)
        .first()
    )
    if not settings:
        settings = ProjectSettings()

    cost = calculate_section_summary(items, settings)
    item_responses = [_item_to_response(item) for item in items]

    total_vlc = cost["vlc"]
    total_nc = cost["nc"]
    total_mtc = cost["mtc"]

    return {
        "id": pkg.id,
        "project_id": pkg.project_id,
        "name": pkg.name,
        "package_type": pkg.package_type,
        "description": pkg.description,
        "sort_order": pkg.sort_order or 0,
        "created_at": pkg.created_at,
        "updated_at": pkg.updated_at,
        "item_count": len(items),
        "total_cost": round(total_vlc + total_nc + total_mtc),
        "vlc": round(total_vlc),
        "nc": round(total_nc),
        "mtc": round(total_mtc),
        "items": item_responses,
        "cost_breakdown": cost,
    }


def create_bid_package(db: Session, project_id: int, data) -> BidPackage:
    """Create a new bid package."""
    pkg = BidPackage(
        project_id=project_id,
        name=data.name,
        package_type=data.package_type,
        description=data.description,
        sort_order=data.sort_order,
    )
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    return pkg


def update_bid_package(db: Session, package_id: int, data) -> BidPackage | None:
    """Update a bid package."""
    pkg = db.query(BidPackage).filter(BidPackage.id == package_id).first()
    if not pkg:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(pkg, key, value)

    db.commit()
    db.refresh(pkg)
    return pkg


def delete_bid_package(db: Session, package_id: int) -> bool:
    """Delete a bid package. Items get bid_package_id=NULL via ON DELETE SET NULL."""
    pkg = db.query(BidPackage).filter(BidPackage.id == package_id).first()
    if not pkg:
        return False
    db.delete(pkg)
    db.commit()
    return True


def assign_items(db: Session, package_id: int, item_ids: list[int]) -> int:
    """Assign items to a bid package. Returns count of updated items."""
    count = (
        db.query(ProjectItem)
        .filter(ProjectItem.id.in_(item_ids))
        .update({ProjectItem.bid_package_id: package_id}, synchronize_session="fetch")
    )
    db.commit()
    return count


def remove_items(db: Session, package_id: int, item_ids: list[int]) -> int:
    """Remove items from a bid package (set bid_package_id=NULL)."""
    count = (
        db.query(ProjectItem)
        .filter(ProjectItem.id.in_(item_ids), ProjectItem.bid_package_id == package_id)
        .update({ProjectItem.bid_package_id: None}, synchronize_session="fetch")
    )
    db.commit()
    return count


def _fmt_num(val: float | int | None) -> str:
    """Format number with thousand separators."""
    if val is None:
        return ""
    return f"{round(val):,}".replace(",", ".")


def generate_bid_package_excel(db: Session, package_id: int) -> io.BytesIO | None:
    """Generate Excel export for a single bid package."""
    pkg = db.query(BidPackage).filter(BidPackage.id == package_id).first()
    if not pkg:
        return None

    items = (
        db.query(ProjectItem)
        .filter(ProjectItem.bid_package_id == pkg.id)
        .order_by(ProjectItem.sort_order)
        .all()
    )

    settings = (
        db.query(ProjectSettings)
        .filter(ProjectSettings.project_id == pkg.project_id)
        .first()
    )
    if not settings:
        settings = ProjectSettings()

    cost = calculate_section_summary(items, settings)

    # Build workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Gói thầu"

    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )
    header_font = Font(bold=True, size=11)
    title_font = Font(bold=True, size=14)
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font_white = Font(bold=True, size=11, color="FFFFFF")
    num_fmt = '#,##0'

    # Title
    ws.merge_cells("A1:I1")
    title_cell = ws["A1"]
    title_cell.value = f"GÓI THẦU: {pkg.name}"
    title_cell.font = title_font
    title_cell.alignment = Alignment(horizontal="center")

    ws.merge_cells("A2:I2")
    ws["A2"].value = f"Loại: {pkg.package_type}"
    ws["A2"].alignment = Alignment(horizontal="center")

    if pkg.description:
        ws.merge_cells("A3:I3")
        ws["A3"].value = pkg.description
        ws["A3"].alignment = Alignment(horizontal="center")

    # Column widths
    col_widths = [6, 14, 40, 8, 10, 16, 16, 16, 18]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[chr(64 + i) if i <= 9 else ""].width = w
    # Fix column width for columns A-I
    from openpyxl.utils import get_column_letter
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # Header row
    headers = ["STT", "Mã hiệu", "Tên công việc", "ĐVT", "KL", "VLC", "NC", "MTC", "Thành tiền"]
    header_row = 5
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col, value=header)
        cell.font = header_font_white
        cell.fill = header_fill
        cell.border = thin_border
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Data rows
    for idx, item in enumerate(items, 1):
        row = header_row + idx
        qty = item.quantity or 0
        eff_vlc = item.override_vlc if item.override_vlc is not None else (item.vlc or 0)
        eff_nc = item.override_nc if item.override_nc is not None else (item.nc or 0)
        eff_mtc = item.override_mtc if item.override_mtc is not None else (item.mtc or 0)
        thanh_tien = round(qty * (eff_vlc + eff_nc + eff_mtc))

        values = [
            idx,
            item.mhdg,
            item.tcv,
            item.dvt,
            qty,
            round(qty * eff_vlc),
            round(qty * eff_nc),
            round(qty * eff_mtc),
            thanh_tien,
        ]
        for col, val in enumerate(values, 1):
            cell = ws.cell(row=row, column=col, value=val)
            cell.border = thin_border
            if col >= 5:
                cell.number_format = num_fmt
                cell.alignment = Alignment(horizontal="right")

    # Summary section
    summary_start = header_row + len(items) + 2
    summary_items = [
        ("Chi phí trực tiếp (T)", cost["t"]),
        ("Chi phí chung (C)", cost["c"]),
        ("Thu nhập chịu thuế tính trước (TL)", cost["tl"]),
        ("Giá trị dự toán xây dựng trước thuế (G)", cost["g"]),
        ("Thuế GTGT", cost["gtgt"]),
        ("Nhà tạm", cost["nha_tam"]),
        ("Giá trị dự toán xây dựng (GXD)", cost["gxd"]),
    ]

    ws.merge_cells(f"A{summary_start}:G{summary_start}")
    ws.cell(row=summary_start, column=1, value="TỔNG HỢP CHI PHÍ").font = Font(bold=True, size=12)

    for i, (label, value) in enumerate(summary_items):
        row = summary_start + 1 + i
        ws.merge_cells(f"A{row}:G{row}")
        label_cell = ws.cell(row=row, column=1, value=label)
        label_cell.border = thin_border
        if label.startswith("Giá trị dự toán xây dựng (GXD)"):
            label_cell.font = Font(bold=True)

        val_cell = ws.cell(row=row, column=8, value=round(value))
        val_cell.number_format = num_fmt
        val_cell.border = thin_border
        val_cell.alignment = Alignment(horizontal="right")
        if label.startswith("Giá trị dự toán xây dựng (GXD)"):
            val_cell.font = Font(bold=True)

        # Merge H and I for value
        ws.merge_cells(f"H{row}:I{row}")

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
