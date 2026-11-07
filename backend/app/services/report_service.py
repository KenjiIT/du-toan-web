# -*- coding: utf-8 -*-
"""Extended report/export templates for construction cost estimation."""

import io
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


def _setup_styles() -> dict:
    """Return a dict of common openpyxl styles used across all reports."""
    return {
        "thin_border": Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        ),
        "header_font": Font(bold=True, size=11),
        "title_font": Font(bold=True, size=14),
        "subtitle_font": Font(bold=True, size=12),
        "header_fill": PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid"),
        "subtotal_fill": PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid"),
        "group_fill": PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid"),
        "number_format": "#,##0",
        "hp_format": "#,##0.0000",
    }


def _write_resource_sheet(ws, title: str, project_name: str, resources: list, total: float, s: dict):
    """Write a single THVT-style resource sheet (vat lieu / nhan cong / may thi cong)."""
    # Title
    ws.merge_cells("A1:G1")
    cell = ws["A1"]
    cell.value = title
    cell.font = s["title_font"]
    cell.alignment = Alignment(horizontal="center")

    ws.merge_cells("A2:G2")
    cell = ws["A2"]
    cell.value = f"Công trình: {project_name}"
    cell.font = s["subtitle_font"]
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
        cell.font = s["header_font"]
        cell.fill = s["header_fill"]
        cell.border = s["thin_border"]
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    # Data rows
    for row_idx, res in enumerate(resources, header_row + 1):
        stt = row_idx - header_row
        values = [
            stt,
            res["msvt"],
            res.get("tvt") or "",
            res.get("dvt") or "",
            res.get("total_hao_phi", 0),
            res.get("gia", 0),
            res.get("thanh_tien", 0),
        ]
        for col_idx, val in enumerate(values, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.border = s["thin_border"]
            if col_idx == 5:
                cell.number_format = s["hp_format"]
                cell.alignment = Alignment(horizontal="right")
            elif col_idx >= 6:
                cell.number_format = s["number_format"]
                cell.alignment = Alignment(horizontal="right")
            elif col_idx == 1:
                cell.alignment = Alignment(horizontal="center")

    # Totals row
    if resources:
        total_row = header_row + len(resources) + 1
        ws.merge_cells(f"A{total_row}:F{total_row}")
        cell = ws.cell(row=total_row, column=1, value="TỔNG CỘNG")
        cell.font = s["header_font"]
        cell.border = s["thin_border"]
        cell.alignment = Alignment(horizontal="center")
        for col_idx in range(2, 7):
            ws.cell(row=total_row, column=col_idx).border = s["thin_border"]

        cell = ws.cell(row=total_row, column=7, value=total)
        cell.font = s["header_font"]
        cell.border = s["thin_border"]
        cell.number_format = s["number_format"]
        cell.alignment = Alignment(horizontal="right")

        # Footer
        footer_row = total_row + 2
        ws.cell(
            row=footer_row, column=7,
            value=f"Ngày xuất: {datetime.now().strftime('%d/%m/%Y')}",
        )


# ---------------------------------------------------------------------------
# 1. Bảng phân tích đơn giá chi tiết
# ---------------------------------------------------------------------------

def generate_phan_tich_don_gia_excel(
    project_name: str,
    items_with_details: list[dict],
) -> io.BytesIO:
    """Generate detailed price analysis Excel for all project items.

    Each item gets a section showing its resource breakdown.
    ``items_with_details`` comes from price_calculator.calculate_unit_price()
    and each dict has keys: mhdg, tcv, dvt, vlc, nc, mtc, total, details.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "PHÂN TÍCH ĐƠN GIÁ"
    s = _setup_styles()

    # Page title
    ws.merge_cells("A1:G1")
    cell = ws["A1"]
    cell.value = "BẢNG PHÂN TÍCH ĐƠN GIÁ CHI TIẾT"
    cell.font = s["title_font"]
    cell.alignment = Alignment(horizontal="center")

    ws.merge_cells("A2:G2")
    cell = ws["A2"]
    cell.value = f"Công trình: {project_name}"
    cell.font = s["subtitle_font"]
    cell.alignment = Alignment(horizontal="center")

    # Column widths (set once)
    col_widths = [6, 16, 45, 10, 14, 16, 20]
    for col_idx, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = w

    row = 4  # start writing items from row 4

    type_labels = {
        "VL": "VẬT LIỆU",
        "NC": "NHÂN CÔNG",
        "MTC": "MÁY THI CÔNG",
    }
    type_order = ["VL", "NC", "MTC"]

    for item_idx, item in enumerate(items_with_details):
        if "error" in item:
            continue

        # --- Item header ---
        ws.merge_cells(f"A{row}:G{row}")
        cell = ws.cell(row=row, column=1)
        cell.value = f"{item_idx + 1}. Mã: {item['mhdg']} - {item.get('tcv', '')}  (ĐVT: {item.get('dvt', '')})"
        cell.font = Font(bold=True, size=11, color="1F4E79")
        cell.alignment = Alignment(wrap_text=True)
        row += 1

        # --- Table header ---
        table_headers = ["STT", "Mã vật tư", "Tên", "ĐVT", "Hao phí", "Đơn giá", "Thành tiền"]
        for col_idx, h in enumerate(table_headers, 1):
            cell = ws.cell(row=row, column=col_idx, value=h)
            cell.font = s["header_font"]
            cell.fill = s["header_fill"]
            cell.border = s["thin_border"]
            cell.alignment = Alignment(horizontal="center", wrap_text=True)
        row += 1

        # --- Group details by type ---
        details = item.get("details", [])
        by_type: dict[str, list] = {}
        for d in details:
            t = d.get("type", "VL")
            by_type.setdefault(t, []).append(d)

        detail_stt = 0
        for rtype in type_order:
            group = by_type.get(rtype)
            if not group:
                continue

            # Group header row
            label = type_labels.get(rtype, rtype)
            ws.merge_cells(f"A{row}:G{row}")
            cell = ws.cell(row=row, column=1, value=label)
            cell.font = Font(bold=True, size=10, italic=True)
            cell.fill = s["group_fill"]
            cell.border = s["thin_border"]
            for c in range(2, 8):
                ws.cell(row=row, column=c).border = s["thin_border"]
                ws.cell(row=row, column=c).fill = s["group_fill"]
            row += 1

            for d in group:
                detail_stt += 1
                values = [
                    detail_stt,
                    d.get("msvt", ""),
                    d.get("tvt", "") or "",
                    d.get("dvt", "") or "",
                    d.get("hao_phi", 0),
                    d.get("gia", 0),
                    d.get("thanh_tien", 0),
                ]
                for col_idx, val in enumerate(values, 1):
                    cell = ws.cell(row=row, column=col_idx, value=val)
                    cell.border = s["thin_border"]
                    if col_idx == 5:
                        cell.number_format = s["hp_format"]
                        cell.alignment = Alignment(horizontal="right")
                    elif col_idx >= 6:
                        cell.number_format = s["number_format"]
                        cell.alignment = Alignment(horizontal="right")
                    elif col_idx == 1:
                        cell.alignment = Alignment(horizontal="center")
                row += 1

        # --- Subtotals ---
        subtotals = [
            ("Chi phí vật liệu (VLC)", item.get("vlc", 0)),
            ("Chi phí nhân công (NC)", item.get("nc", 0)),
            ("Chi phí máy thi công (MTC)", item.get("mtc", 0)),
        ]
        for label, val in subtotals:
            ws.merge_cells(f"A{row}:F{row}")
            cell = ws.cell(row=row, column=1, value=label)
            cell.font = Font(italic=True, size=10)
            cell.border = s["thin_border"]
            cell.alignment = Alignment(horizontal="right")
            for c in range(2, 7):
                ws.cell(row=row, column=c).border = s["thin_border"]
            cell = ws.cell(row=row, column=7, value=val)
            cell.border = s["thin_border"]
            cell.number_format = s["number_format"]
            cell.alignment = Alignment(horizontal="right")
            row += 1

        # Total row
        ws.merge_cells(f"A{row}:F{row}")
        cell = ws.cell(row=row, column=1, value="ĐƠN GIÁ TỔNG HỢP")
        cell.font = s["header_font"]
        cell.fill = s["subtotal_fill"]
        cell.border = s["thin_border"]
        cell.alignment = Alignment(horizontal="right")
        for c in range(2, 7):
            ws.cell(row=row, column=c).border = s["thin_border"]
            ws.cell(row=row, column=c).fill = s["subtotal_fill"]
        cell = ws.cell(row=row, column=7, value=item.get("total", 0))
        cell.font = s["header_font"]
        cell.fill = s["subtotal_fill"]
        cell.border = s["thin_border"]
        cell.number_format = s["number_format"]
        cell.alignment = Alignment(horizontal="right")
        row += 2  # blank row between items

    # Footer
    ws.cell(row=row, column=7, value=f"Ngày xuất: {datetime.now().strftime('%d/%m/%Y')}")

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# 2. Bảng tổng hợp nhân công
# ---------------------------------------------------------------------------

def generate_nhan_cong_excel(
    project_name: str,
    nhan_cong_list: list[dict],
    total_nc: float,
) -> io.BytesIO:
    """Generate Labor Summary Excel (same format as THVT but N* resources only)."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Nhân công"
    s = _setup_styles()

    _write_resource_sheet(
        ws,
        title="TỔNG HỢP NHÂN CÔNG",
        project_name=project_name,
        resources=nhan_cong_list,
        total=total_nc,
        s=s,
    )

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# 3. Bảng tổng hợp ca máy
# ---------------------------------------------------------------------------

def generate_ca_may_excel(
    project_name: str,
    may_thi_cong_list: list[dict],
    total_mtc: float,
) -> io.BytesIO:
    """Generate Machine Summary Excel (same format as THVT but M* resources only)."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Máy thi công"
    s = _setup_styles()

    _write_resource_sheet(
        ws,
        title="TỔNG HỢP CA MÁY THI CÔNG",
        project_name=project_name,
        resources=may_thi_cong_list,
        total=total_mtc,
        s=s,
    )

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# 4. Bảng tổng hợp dự toán (full report, multi-sheet)
# ---------------------------------------------------------------------------

def _write_du_toan_sheet(ws, project_name: str, items: list[dict], summary: dict, s: dict):
    """Write Sheet 1 — Bảng dự toán (items table)."""
    ws.merge_cells("A1:L1")
    cell = ws["A1"]
    cell.value = "BẢNG DỰ TOÁN CHI PHÍ XÂY DỰNG"
    cell.font = s["title_font"]
    cell.alignment = Alignment(horizontal="center")

    ws.merge_cells("A2:L2")
    cell = ws["A2"]
    cell.value = f"Công trình: {project_name}"
    cell.font = s["subtitle_font"]
    cell.alignment = Alignment(horizontal="center")

    headers = [
        ("STT", 6),
        ("Mã hiệu", 14),
        ("Tên công việc", 40),
        ("ĐVT", 8),
        ("Khối lượng", 12),
        ("ĐG Vật liệu", 14),
        ("ĐG Nhân công", 14),
        ("ĐG Máy TC", 14),
        ("TT Vật liệu", 16),
        ("TT Nhân công", 16),
        ("TT Máy TC", 16),
        ("Thành tiền", 18),
    ]

    header_row = 4
    for col_idx, (header_text, width) in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col_idx, value=header_text)
        cell.font = s["header_font"]
        cell.fill = s["header_fill"]
        cell.border = s["thin_border"]
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    for row_idx, item in enumerate(items, header_row + 1):
        stt = row_idx - header_row
        qty = item.get("quantity", 0)
        vlc = item.get("vlc") or 0
        nc = item.get("nc") or 0
        mtc = item.get("mtc") or 0
        tt_vlc = item.get("thanh_tien_vlc") or round(qty * vlc)
        tt_nc = item.get("thanh_tien_nc") or round(qty * nc)
        tt_mtc = item.get("thanh_tien_mtc") or round(qty * mtc)
        tt = item.get("thanh_tien") or (tt_vlc + tt_nc + tt_mtc)

        values = [stt, item.get("mhdg", ""), item.get("tcv", ""), item.get("dvt", ""),
                  qty, vlc, nc, mtc, tt_vlc, tt_nc, tt_mtc, tt]
        for col_idx, val in enumerate(values, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.border = s["thin_border"]
            if col_idx >= 5:
                cell.number_format = s["number_format"]
                cell.alignment = Alignment(horizontal="right")
            elif col_idx == 1:
                cell.alignment = Alignment(horizontal="center")

    if items:
        total_row = header_row + len(items) + 1
        ws.merge_cells(f"A{total_row}:D{total_row}")
        cell = ws.cell(row=total_row, column=1, value="TỔNG CỘNG")
        cell.font = s["header_font"]
        cell.border = s["thin_border"]
        cell.alignment = Alignment(horizontal="center")
        for col_idx in range(2, 5):
            ws.cell(row=total_row, column=col_idx).border = s["thin_border"]

        totals = [None, None, None, None,
                  summary.get("vlc", 0), summary.get("nc", 0),
                  summary.get("mtc", 0), summary.get("t", 0)]
        for col_offset, val in enumerate(totals):
            col = 5 + col_offset
            cell = ws.cell(row=total_row, column=col, value=val)
            cell.border = s["thin_border"]
            cell.font = s["header_font"]
            if val is not None:
                cell.number_format = s["number_format"]
                cell.alignment = Alignment(horizontal="right")


def _write_kinh_phi_sheet(ws, project_name: str, summary: dict, s: dict):
    """Write the cost summary sheet (Tổng hợp kinh phí)."""
    ws.merge_cells("A1:C1")
    cell = ws["A1"]
    cell.value = "TỔNG HỢP KINH PHÍ XÂY DỰNG"
    cell.font = s["title_font"]
    cell.alignment = Alignment(horizontal="center")

    ws.merge_cells("A2:C2")
    cell = ws["A2"]
    cell.value = f"Công trình: {project_name}"
    cell.font = s["subtitle_font"]
    cell.alignment = Alignment(horizontal="center")

    summary_headers = ["Khoản mục", "Ký hiệu", "Giá trị (đồng)"]
    for col_idx, h in enumerate(summary_headers, 1):
        cell = ws.cell(row=4, column=col_idx, value=h)
        cell.font = s["header_font"]
        cell.fill = s["header_fill"]
        cell.border = s["thin_border"]
        cell.alignment = Alignment(horizontal="center")

    ws.column_dimensions["A"].width = 40
    ws.column_dimensions["B"].width = 12
    ws.column_dimensions["C"].width = 22

    summary_rows = [
        ("Chi phí vật liệu", "VLC", summary.get("vlc", 0)),
        ("Chi phí nhân công", "NC", summary.get("nc", 0)),
        ("Chi phí máy thi công", "MTC", summary.get("mtc", 0)),
        (
            f"Trực tiếp phí khác ({summary.get('truc_tiep_khac_pct', 2.5)}%)",
            "TTPK",
            summary.get("truc_tiep_khac", 0),
        ),
        ("Chi phí trực tiếp (T = VLC + NC + MTC + TTPK)", "T", summary.get("t", 0)),
        (
            f"Chi phí chung ({summary.get('chi_phi_chung_pct', 6.5)}% x T)",
            "C",
            summary.get("c", 0),
        ),
        (
            f"Thu nhập chịu thuế tính trước ({summary.get('thu_nhap_tt_pct', 5.5)}% x (T+C))",
            "TL",
            summary.get("tl", 0),
        ),
        ("Giá trị dự toán XD trước thuế (G = T + C + TL)", "G", summary.get("g", 0)),
        (
            f"Thuế GTGT ({summary.get('vat_pct', 10)}% x G)",
            "GTGT",
            summary.get("gtgt", 0),
        ),
        (
            f"Chi phí nhà tạm ({summary.get('nha_tam_pct', 1)}% x G)",
            "NT",
            summary.get("nha_tam", 0),
        ),
        ("GIÁ TRỊ DỰ TOÁN XÂY DỰNG SAU THUẾ", "GXD", summary.get("gxd", 0)),
    ]

    for row_idx, (label, symbol, value) in enumerate(summary_rows, 5):
        cell_a = ws.cell(row=row_idx, column=1, value=label)
        cell_b = ws.cell(row=row_idx, column=2, value=symbol)
        cell_c = ws.cell(row=row_idx, column=3, value=value)
        cell_a.border = s["thin_border"]
        cell_b.border = s["thin_border"]
        cell_b.alignment = Alignment(horizontal="center")
        cell_c.border = s["thin_border"]
        cell_c.number_format = s["number_format"]
        cell_c.alignment = Alignment(horizontal="right")

        if symbol in ("T", "G", "GXD"):
            cell_a.font = s["header_font"]
            cell_b.font = s["header_font"]
            cell_c.font = s["header_font"]

    last_row = 5 + len(summary_rows) + 1
    ws.cell(row=last_row, column=3, value=f"Ngày xuất: {datetime.now().strftime('%d/%m/%Y')}")


def _write_tmdt_sheet(ws, project_name: str, tmdt_data: dict, s: dict):
    """Write the TMDT sheet (Tổng mức đầu tư)."""
    ws.merge_cells("A1:D1")
    cell = ws["A1"]
    cell.value = "TỔNG MỨC ĐẦU TƯ"
    cell.font = s["title_font"]
    cell.alignment = Alignment(horizontal="center")

    ws.merge_cells("A2:D2")
    cell = ws["A2"]
    cell.value = f"Công trình: {project_name}"
    cell.font = s["subtitle_font"]
    cell.alignment = Alignment(horizontal="center")

    headers = ["STT", "Khoản mục chi phí", "Cách tính", "Thành tiền (đồng)"]
    widths = [8, 45, 20, 22]
    for col_idx, (h, w) in enumerate(zip(headers, widths), 1):
        cell = ws.cell(row=4, column=col_idx, value=h)
        cell.font = s["header_font"]
        cell.fill = s["header_fill"]
        cell.border = s["thin_border"]
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(col_idx)].width = w

    row = 5
    stt = 0

    # G_XD row
    stt += 1
    for col, val in enumerate([stt, "Chi phí xây dựng (GXD)", "Từ dự toán", tmdt_data["g_xd"]], 1):
        c = ws.cell(row=row, column=col, value=val)
        c.border = s["thin_border"]
        c.font = s["header_font"]
        if col == 4:
            c.number_format = s["number_format"]
            c.alignment = Alignment(horizontal="right")
    row += 1

    for cat_data in tmdt_data.get("categories", []):
        stt += 1
        for col, val in enumerate([stt, cat_data["label"], "", cat_data["subtotal"]], 1):
            c = ws.cell(row=row, column=col, value=val)
            c.border = s["thin_border"]
            c.font = s["header_font"]
            if col == 4:
                c.number_format = s["number_format"]
                c.alignment = Alignment(horizontal="right")
        row += 1

        for item in cat_data.get("items", []):
            calc_desc = ""
            if item["calc_type"] == "percent" and item.get("percent_value") is not None:
                base_label = "tổng trước DP" if cat_data["category"] == "du_phong" else "GXD"
                calc_desc = f"{item['percent_value']}% x {base_label}"
            else:
                calc_desc = "Cố định"
            for col, val in enumerate(["", f"  - {item['name']}", calc_desc, item["amount"]], 1):
                c = ws.cell(row=row, column=col, value=val)
                c.border = s["thin_border"]
                if col == 4:
                    c.number_format = s["number_format"]
                    c.alignment = Alignment(horizontal="right")
            row += 1

    # Subtotal before DP
    row += 1
    for col, val in enumerate(["", "Tổng trước dự phòng", "", tmdt_data["subtotal_before_dp"]], 1):
        c = ws.cell(row=row, column=col, value=val)
        c.border = s["thin_border"]
        c.font = s["header_font"]
        c.fill = s["subtotal_fill"]
        if col == 4:
            c.number_format = s["number_format"]
            c.alignment = Alignment(horizontal="right")
    row += 1

    # TMDT total
    for col, val in enumerate(["", "TỔNG MỨC ĐẦU TƯ (TMĐT)", "", tmdt_data["tmdt"]], 1):
        c = ws.cell(row=row, column=col, value=val)
        c.border = s["thin_border"]
        c.font = Font(bold=True, size=12)
        c.fill = s["subtotal_fill"]
        if col == 4:
            c.number_format = s["number_format"]
            c.alignment = Alignment(horizontal="right")
    row += 2

    ws.cell(row=row, column=4, value=f"Ngày xuất: {datetime.now().strftime('%d/%m/%Y')}")


def generate_full_report_excel(
    project_name: str,
    items_data: list[dict],
    thvt_data: dict,
    summary: dict,
    tmdt_data: dict | None = None,
) -> io.BytesIO:
    """Generate the multi-sheet overall summary workbook.

    Sheets:
        1. BẢNG DỰ TOÁN         — project items
        2. TỔNG HỢP VẬT TƯ     — materials
        3. TỔNG HỢP NHÂN CÔNG   — labor
        4. TỔNG HỢP CA MÁY      — machines
        5. TỔNG HỢP KINH PHÍ    — cost summary
        6. TỔNG MỨC ĐẦU TƯ     — (only if tmdt_data provided)
    """
    wb = Workbook()
    s = _setup_styles()

    # Sheet 1: Bảng dự toán
    ws1 = wb.active
    ws1.title = "BẢNG DỰ TOÁN"
    _write_du_toan_sheet(ws1, project_name, items_data, summary, s)

    # Sheet 2: Tổng hợp vật tư
    ws2 = wb.create_sheet("TỔNG HỢP VẬT TƯ")
    _write_resource_sheet(
        ws2,
        title="TỔNG HỢP VẬT TƯ",
        project_name=project_name,
        resources=thvt_data.get("vat_lieu", []),
        total=thvt_data.get("total_vl", 0),
        s=s,
    )

    # Sheet 3: Tổng hợp nhân công
    ws3 = wb.create_sheet("TỔNG HỢP NHÂN CÔNG")
    _write_resource_sheet(
        ws3,
        title="TỔNG HỢP NHÂN CÔNG",
        project_name=project_name,
        resources=thvt_data.get("nhan_cong", []),
        total=thvt_data.get("total_nc", 0),
        s=s,
    )

    # Sheet 4: Tổng hợp ca máy
    ws4 = wb.create_sheet("TỔNG HỢP CA MÁY")
    _write_resource_sheet(
        ws4,
        title="TỔNG HỢP CA MÁY THI CÔNG",
        project_name=project_name,
        resources=thvt_data.get("may_thi_cong", []),
        total=thvt_data.get("total_mtc", 0),
        s=s,
    )

    # Sheet 5: Tổng hợp kinh phí
    ws5 = wb.create_sheet("TỔNG HỢP KINH PHÍ")
    _write_kinh_phi_sheet(ws5, project_name, summary, s)

    # Sheet 6: Tổng mức đầu tư (optional)
    if tmdt_data is not None:
        ws6 = wb.create_sheet("TỔNG MỨC ĐẦU TƯ")
        _write_tmdt_sheet(ws6, project_name, tmdt_data, s)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# 5. Bang quyet toan (Settlement report)
# ---------------------------------------------------------------------------

def generate_settlement_excel(project_name: str, settlement_data: dict) -> io.BytesIO:
    """Generate settlement comparison Excel report."""
    wb = Workbook()
    ws = wb.active
    ws.title = "QUYẾT TOÁN"
    s = _setup_styles()

    # Title
    ws.merge_cells("A1:L1")
    cell = ws["A1"]
    cell.value = "BẢNG QUYẾT TOÁN - SO SÁNH KHỐI LƯỢNG"
    cell.font = s["title_font"]
    cell.alignment = Alignment(horizontal="center")

    ws.merge_cells("A2:L2")
    cell = ws["A2"]
    cell.value = f"Công trình: {project_name}"
    cell.font = s["subtitle_font"]
    cell.alignment = Alignment(horizontal="center")

    # Summary section
    ws.merge_cells("A4:B4")
    ws["A4"].value = "Tổng dự toán:"
    ws["A4"].font = s["header_font"]
    ws["C4"].value = settlement_data.get("total_du_toan", 0)
    ws["C4"].number_format = s["number_format"]

    ws.merge_cells("A5:B5")
    ws["A5"].value = "Tổng thực tế:"
    ws["A5"].font = s["header_font"]
    ws["C5"].value = settlement_data.get("total_thuc_te", 0)
    ws["C5"].number_format = s["number_format"]

    ws.merge_cells("A6:B6")
    ws["A6"].value = "Chênh lệch:"
    ws["A6"].font = s["header_font"]
    ws["C6"].value = settlement_data.get("total_chenh_lech", 0)
    ws["C6"].number_format = s["number_format"]
    chenh_lech_val = settlement_data.get("total_chenh_lech", 0)
    if chenh_lech_val > 0:
        ws["C6"].font = Font(bold=True, color="FF0000")
    elif chenh_lech_val < 0:
        ws["C6"].font = Font(bold=True, color="008000")

    ws.merge_cells("A7:B7")
    ws["A7"].value = "% hoàn thành:"
    ws["A7"].font = s["header_font"]
    ws["C7"].value = f"{settlement_data.get('pct_hoan_thanh', 0)}%"

    # Headers
    headers = [
        ("STT", 6), ("Mã hiệu", 14), ("Tên công việc", 35), ("ĐVT", 8),
        ("KL dự toán", 14), ("KL thực tế", 14), ("Đơn giá", 14),
        ("TT Dự toán", 16), ("TT Thực tế", 16), ("Chênh lệch", 16),
        ("Ngày NT", 12), ("Ghi chú", 20),
    ]

    header_row = 9
    for col_idx, (h, w) in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col_idx, value=h)
        cell.font = s["header_font"]
        cell.fill = s["header_fill"]
        cell.border = s["thin_border"]
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(col_idx)].width = w

    # Data rows
    items = settlement_data.get("items", [])
    for row_idx, item in enumerate(items, header_row + 1):
        stt = row_idx - header_row
        acc_date = item.get("acceptance_date")
        if acc_date and hasattr(acc_date, "strftime"):
            acc_date_str = acc_date.strftime("%d/%m/%Y")
        else:
            acc_date_str = str(acc_date) if acc_date else ""
        values = [
            stt, item.get("mhdg", ""), item.get("tcv", ""), item.get("dvt", ""),
            item.get("quantity", 0), item.get("actual_quantity") or 0,
            item.get("unit_price", 0),
            item.get("thanh_tien_du_toan", 0), item.get("thanh_tien_thuc_te", 0),
            item.get("chenh_lech", 0),
            acc_date_str,
            item.get("acceptance_notes") or "",
        ]
        for col_idx, val in enumerate(values, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.border = s["thin_border"]
            if col_idx in (5, 6, 7, 8, 9, 10):
                cell.number_format = s["number_format"]
                cell.alignment = Alignment(horizontal="right")
            elif col_idx == 1:
                cell.alignment = Alignment(horizontal="center")
            # Color code chenh lech
            if col_idx == 10:
                cl = item.get("chenh_lech", 0)
                if cl > 0:
                    cell.font = Font(color="FF0000")
                elif cl < 0:
                    cell.font = Font(color="008000")

    # Footer
    if items:
        footer_row = header_row + len(items) + 2
        ws.cell(row=footer_row, column=12, value=f"Ngày xuất: {datetime.now().strftime('%d/%m/%Y')}")

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# 6. Mau 01 - Tong hop du toan xay dung cong trinh
# ---------------------------------------------------------------------------

def _write_gov_header(ws, s, title: str, project_name: str, metadata: dict, max_col: str = "F"):
    """Write standard government report header with investor/location info."""
    row = 1
    ws.merge_cells(f"A{row}:{max_col}{row}")
    cell = ws[f"A{row}"]
    cell.value = metadata.get("chu_dau_tu") or "Chủ đầu tư: _______________"
    cell.font = Font(bold=True, size=11)
    cell.alignment = Alignment(horizontal="center")
    row += 2

    ws.merge_cells(f"A{row}:{max_col}{row}")
    cell = ws[f"A{row}"]
    cell.value = title
    cell.font = s["title_font"]
    cell.alignment = Alignment(horizontal="center")
    row += 1

    ws.merge_cells(f"A{row}:{max_col}{row}")
    cell = ws[f"A{row}"]
    cell.value = f"Công trình: {project_name}"
    cell.font = s["subtitle_font"]
    cell.alignment = Alignment(horizontal="center")
    row += 1

    if metadata.get("dia_diem"):
        ws.merge_cells(f"A{row}:{max_col}{row}")
        cell = ws[f"A{row}"]
        cell.value = f"Địa điểm: {metadata['dia_diem']}"
        cell.alignment = Alignment(horizontal="center")
        row += 1

    return row + 1  # return next available row


def _write_gov_footer(ws, s, row: int, metadata: dict, max_col_idx: int = 6):
    """Write standard government report footer with signatures."""
    row += 1
    ws.cell(row=row, column=max_col_idx, value=f"Ngày ... tháng ... năm {datetime.now().year}")
    ws.cell(row=row, column=max_col_idx).alignment = Alignment(horizontal="center")
    row += 1

    # Signature blocks
    sig_cols = []
    if metadata.get("nguoi_lap"):
        sig_cols.append(("NGƯỜI LẬP", metadata["nguoi_lap"], 1))
    if metadata.get("nguoi_kiem_tra"):
        sig_cols.append(("NGƯỜI KIỂM TRA", metadata["nguoi_kiem_tra"], 3))
    if metadata.get("chu_dau_tu"):
        sig_cols.append(("CHỦ ĐẦU TƯ", metadata["chu_dau_tu"], max_col_idx - 1))

    for title_text, name, col in sig_cols:
        cell = ws.cell(row=row, column=col, value=title_text)
        cell.font = s["header_font"]
        cell.alignment = Alignment(horizontal="center")
        ws.cell(row=row + 3, column=col, value=name).alignment = Alignment(horizontal="center")

    return row + 4


def generate_mau_01_excel(
    project_name: str,
    metadata: dict,
    tmdt_data: dict,
    summary: dict,
) -> io.BytesIO:
    """Mau 01: Tong hop du toan xay dung cong trinh."""
    wb = Workbook()
    ws = wb.active
    ws.title = "MẪU 01"
    s = _setup_styles()
    ws.page_setup.paperSize = ws.PAPERSIZE_A4

    row = _write_gov_header(ws, s, "TỔNG HỢP DỰ TOÁN XÂY DỰNG CÔNG TRÌNH", project_name, metadata, "F")

    # Column headers
    headers = [
        ("STT", 6), ("Nội dung chi phí", 35), ("Cách tính", 20),
        ("Giá trị (trước thuế)", 18), ("Thuế GTGT", 16), ("Giá trị (sau thuế)", 18),
    ]
    for col_idx, (h, w) in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col_idx, value=h)
        cell.font = s["header_font"]
        cell.fill = s["header_fill"]
        cell.border = s["thin_border"]
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(col_idx)].width = w
    row += 1

    vat_pct = summary.get("vat_pct", 10)
    g_before_tax = summary.get("g", 0)
    gtgt = summary.get("gtgt", 0)
    gxd = summary.get("gxd", 0)

    # Row data
    cost_rows = [
        ("I", "Chi phí xây dựng (GXD)", "Từ dự toán", g_before_tax, gtgt, gxd),
    ]

    # Add TMDT categories if available
    stt_map = ["II", "III", "IV", "V", "VI"]
    for i, cat in enumerate(tmdt_data.get("categories", [])):
        stt_label = stt_map[i] if i < len(stt_map) else str(i + 2)
        subtotal = cat.get("subtotal", 0)
        vat_amount = round(subtotal * vat_pct / 100)
        cost_rows.append((stt_label, cat["label"], "", subtotal, vat_amount, subtotal + vat_amount))

    # TMDT total
    tmdt_val = tmdt_data.get("tmdt", gxd)

    for stt_label, name, calc, before_tax, vat_val, after_tax in cost_rows:
        values = [stt_label, name, calc, before_tax, vat_val, after_tax]
        for col_idx, val in enumerate(values, 1):
            cell = ws.cell(row=row, column=col_idx, value=val)
            cell.border = s["thin_border"]
            if col_idx >= 4:
                cell.number_format = s["number_format"]
                cell.alignment = Alignment(horizontal="right")
            elif col_idx == 1:
                cell.alignment = Alignment(horizontal="center")
                cell.font = s["header_font"]
        row += 1

    # Total row
    row += 1
    ws.merge_cells(f"A{row}:C{row}")
    cell = ws.cell(row=row, column=1, value="TỔNG MỨC ĐẦU TƯ")
    cell.font = Font(bold=True, size=12)
    cell.border = s["thin_border"]
    for c in range(2, 4):
        ws.cell(row=row, column=c).border = s["thin_border"]
    ws.cell(row=row, column=4, value=tmdt_val).border = s["thin_border"]
    ws.cell(row=row, column=4).number_format = s["number_format"]
    ws.cell(row=row, column=4).font = Font(bold=True, size=12)
    ws.cell(row=row, column=4).alignment = Alignment(horizontal="right")
    ws.cell(row=row, column=5).border = s["thin_border"]
    ws.cell(row=row, column=6).border = s["thin_border"]
    row += 2

    _write_gov_footer(ws, s, row, metadata, 6)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# 7. Mau 02 - Bang tinh chi phi xay dung
# ---------------------------------------------------------------------------

def generate_mau_02_excel(
    project_name: str,
    metadata: dict,
    items_data: list[dict],
    summary: dict,
) -> io.BytesIO:
    """Mau 02: Bang tinh chi phi xay dung."""
    wb = Workbook()
    ws = wb.active
    ws.title = "MẪU 02"
    s = _setup_styles()
    ws.page_setup.paperSize = ws.PAPERSIZE_A4

    row = _write_gov_header(ws, s, "BẢNG TÍNH CHI PHÍ XÂY DỰNG", project_name, metadata, "K")

    # Column headers
    headers = [
        ("STT", 6), ("Mã hiệu", 14), ("Tên công việc", 35), ("ĐVT", 8),
        ("Khối lượng", 12), ("ĐG VLC", 14), ("ĐG NC", 14), ("ĐG MTC", 14),
        ("TT VLC", 16), ("TT NC", 16), ("Thành tiền", 18),
    ]
    for col_idx, (h, w) in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col_idx, value=h)
        cell.font = s["header_font"]
        cell.fill = s["header_fill"]
        cell.border = s["thin_border"]
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(col_idx)].width = w
    row += 1

    # Data rows
    for item_idx, item in enumerate(items_data, 1):
        qty = item.get("quantity", 0)
        vlc = item.get("vlc") or 0
        nc = item.get("nc") or 0
        mtc = item.get("mtc") or 0
        tt_vlc = item.get("thanh_tien_vlc") or round(qty * vlc)
        tt_nc = item.get("thanh_tien_nc") or round(qty * nc)
        tt = item.get("thanh_tien") or (tt_vlc + tt_nc + round(qty * mtc))

        values = [
            item_idx, item.get("mhdg", ""), item.get("tcv", ""), item.get("dvt", ""),
            qty, vlc, nc, mtc, tt_vlc, tt_nc, tt,
        ]
        for col_idx, val in enumerate(values, 1):
            cell = ws.cell(row=row, column=col_idx, value=val)
            cell.border = s["thin_border"]
            if col_idx >= 5:
                cell.number_format = s["number_format"]
                cell.alignment = Alignment(horizontal="right")
            elif col_idx == 1:
                cell.alignment = Alignment(horizontal="center")
        row += 1

    # Summary rows
    row += 1
    summary_rows = [
        ("Chi phí vật liệu (VLC)", summary.get("vlc", 0)),
        ("Chi phí nhân công (NC)", summary.get("nc", 0)),
        ("Chi phí máy thi công (MTC)", summary.get("mtc", 0)),
        ("Chi phí trực tiếp (T)", summary.get("t", 0)),
        ("Chi phí chung (C)", summary.get("c", 0)),
        ("Thu nhập chịu thuế tính trước (TL)", summary.get("tl", 0)),
        ("Giá trị dự toán trước thuế (G)", summary.get("g", 0)),
        ("Thuế GTGT", summary.get("gtgt", 0)),
        ("Chi phí nhà tạm", summary.get("nha_tam", 0)),
        ("GIÁ TRỊ DỰ TOÁN XÂY DỰNG (GXD)", summary.get("gxd", 0)),
    ]
    for label, val in summary_rows:
        ws.merge_cells(f"A{row}:J{row}")
        cell = ws.cell(row=row, column=1, value=label)
        cell.border = s["thin_border"]
        for c in range(2, 11):
            ws.cell(row=row, column=c).border = s["thin_border"]
        cell_val = ws.cell(row=row, column=11, value=val)
        cell_val.border = s["thin_border"]
        cell_val.number_format = s["number_format"]
        cell_val.alignment = Alignment(horizontal="right")
        if label.startswith("GIÁ TRỊ") or label.startswith("Chi phí trực tiếp"):
            cell.font = s["header_font"]
            cell_val.font = s["header_font"]
        row += 1

    row += 1
    _write_gov_footer(ws, s, row, metadata, 11)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# 8. Mau 03 - Bang tong hop khoi luong - don gia
# ---------------------------------------------------------------------------

def generate_mau_03_excel(
    project_name: str,
    metadata: dict,
    items_data: list[dict],
) -> io.BytesIO:
    """Mau 03: Bang tong hop khoi luong - don gia."""
    wb = Workbook()
    ws = wb.active
    ws.title = "MẪU 03"
    s = _setup_styles()
    ws.page_setup.paperSize = ws.PAPERSIZE_A4

    row = _write_gov_header(ws, s, "BẢNG TỔNG HỢP KHỐI LƯỢNG - ĐƠN GIÁ", project_name, metadata, "J")

    # Column headers
    headers = [
        ("STT", 6), ("Mã hiệu", 14), ("Tên công việc", 35), ("ĐVT", 8),
        ("Khối lượng", 12), ("CP Vật liệu", 14), ("CP Nhân công", 14),
        ("CP Máy", 14), ("Đơn giá", 16), ("Thành tiền", 18),
    ]
    for col_idx, (h, w) in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col_idx, value=h)
        cell.font = s["header_font"]
        cell.fill = s["header_fill"]
        cell.border = s["thin_border"]
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(col_idx)].width = w
    row += 1

    total_thanh_tien = 0

    for item_idx, item in enumerate(items_data, 1):
        qty = item.get("quantity", 0)
        vlc = item.get("vlc") or 0
        nc = item.get("nc") or 0
        mtc = item.get("mtc") or 0
        don_gia = vlc + nc + mtc
        thanh_tien = item.get("thanh_tien") or round(qty * don_gia)
        total_thanh_tien += thanh_tien

        values = [
            item_idx, item.get("mhdg", ""), item.get("tcv", ""), item.get("dvt", ""),
            qty, vlc, nc, mtc, don_gia, thanh_tien,
        ]
        for col_idx, val in enumerate(values, 1):
            cell = ws.cell(row=row, column=col_idx, value=val)
            cell.border = s["thin_border"]
            if col_idx >= 5:
                cell.number_format = s["number_format"]
                cell.alignment = Alignment(horizontal="right")
            elif col_idx == 1:
                cell.alignment = Alignment(horizontal="center")
        row += 1

    # Total row
    row += 1
    ws.merge_cells(f"A{row}:I{row}")
    cell = ws.cell(row=row, column=1, value="TỔNG CỘNG")
    cell.font = s["header_font"]
    cell.fill = s["subtotal_fill"]
    cell.border = s["thin_border"]
    cell.alignment = Alignment(horizontal="center")
    for c in range(2, 10):
        ws.cell(row=row, column=c).border = s["thin_border"]
        ws.cell(row=row, column=c).fill = s["subtotal_fill"]
    cell_total = ws.cell(row=row, column=10, value=total_thanh_tien)
    cell_total.font = s["header_font"]
    cell_total.fill = s["subtotal_fill"]
    cell_total.border = s["thin_border"]
    cell_total.number_format = s["number_format"]
    cell_total.alignment = Alignment(horizontal="right")
    row += 2

    _write_gov_footer(ws, s, row, metadata, 10)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
