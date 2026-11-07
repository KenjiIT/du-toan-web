"""Export service for generating Excel and PDF reports."""

import io
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _register_vn_font():
    """Register a Vietnamese-capable font for reportlab."""
    try:
        pdfmetrics.getFont("DejaVuSans")
    except KeyError:
        import os

        # Try common locations for DejaVuSans (ships with many systems)
        candidates = [
            os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "arial.ttf"),
            os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "times.ttf"),
            # DejaVu if available
            r"C:\Windows\Fonts\DejaVuSans.ttf",
        ]
        # Also try to find in reportlab's bundled fonts
        try:
            from reportlab.rl_config import TTFSearchPath

            for p in TTFSearchPath:
                candidates.append(os.path.join(p, "DejaVuSans.ttf"))
        except Exception:
            pass

        for path in candidates:
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont("DejaVuSans", path))
                    return "DejaVuSans"
                except Exception:
                    continue

        # Fallback: use Arial which supports Vietnamese on Windows
        arial_path = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "arial.ttf")
        if os.path.exists(arial_path):
            pdfmetrics.registerFont(TTFont("ArialVN", arial_path))
            return "ArialVN"

    return "DejaVuSans"


def _fmt_num(val: float | int | None) -> str:
    """Format number with thousand separators."""
    if val is None:
        return ""
    return f"{round(val):,}".replace(",", ".")


def generate_excel(
    project: dict,
    items: list[dict],
    summary: dict,
) -> io.BytesIO:
    """Generate an Excel workbook mimicking GXD style.

    Args:
        project: dict with keys name, description
        items: list of item dicts (mhdg, tcv, dvt, quantity, vlc, nc, mtc, thanh_tien_vlc, ...)
        summary: cost summary dict

    Returns:
        BytesIO buffer containing the .xlsx file
    """
    wb = Workbook()

    # --- Sheet 1: BẢNG DỰ TOÁN ---
    ws1 = wb.active
    ws1.title = "BẢNG DỰ TOÁN"

    # Styles
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

    # Title rows
    ws1.merge_cells("A1:L1")
    cell = ws1["A1"]
    cell.value = "BẢNG DỰ TOÁN CHI PHÍ XÂY DỰNG"
    cell.font = title_font
    cell.alignment = Alignment(horizontal="center")

    ws1.merge_cells("A2:L2")
    cell = ws1["A2"]
    cell.value = f"Công trình: {project.get('name', '')}"
    cell.font = Font(bold=True, size=12)
    cell.alignment = Alignment(horizontal="center")

    if project.get("description"):
        ws1.merge_cells("A3:L3")
        cell = ws1["A3"]
        cell.value = project["description"]
        cell.alignment = Alignment(horizontal="center")

    # Column headers
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

    header_row = 5
    for col_idx, (header_text, width) in enumerate(headers, 1):
        cell = ws1.cell(row=header_row, column=col_idx, value=header_text)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        ws1.column_dimensions[get_column_letter(col_idx)].width = width

    # Data rows
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

        values = [
            stt,
            item.get("mhdg", ""),
            item.get("tcv", ""),
            item.get("dvt", ""),
            qty,
            vlc,
            nc,
            mtc,
            tt_vlc,
            tt_nc,
            tt_mtc,
            tt,
        ]

        for col_idx, val in enumerate(values, 1):
            cell = ws1.cell(row=row_idx, column=col_idx, value=val)
            cell.border = thin_border
            if col_idx >= 5:  # numeric columns
                cell.number_format = number_format
                cell.alignment = Alignment(horizontal="right")
            elif col_idx == 1:
                cell.alignment = Alignment(horizontal="center")

    # Totals row
    if items:
        total_row = header_row + len(items) + 1
        ws1.merge_cells(f"A{total_row}:D{total_row}")
        cell = ws1.cell(row=total_row, column=1, value="TỔNG CỘNG")
        cell.font = header_font
        cell.border = thin_border
        cell.alignment = Alignment(horizontal="center")

        for col_idx in range(2, 5):
            ws1.cell(row=total_row, column=col_idx).border = thin_border

        totals = [
            None,  # col 5 - qty
            None,  # col 6 - dg vlc
            None,  # col 7 - dg nc
            None,  # col 8 - dg mtc
            summary.get("vlc", 0),
            summary.get("nc", 0),
            summary.get("mtc", 0),
            summary.get("t", 0),
        ]
        for col_offset, val in enumerate(totals):
            col = 5 + col_offset
            cell = ws1.cell(row=total_row, column=col, value=val)
            cell.border = thin_border
            cell.font = header_font
            if val is not None:
                cell.number_format = number_format
                cell.alignment = Alignment(horizontal="right")

    # --- Sheet 2: TỔNG HỢP KINH PHÍ ---
    ws2 = wb.create_sheet("TỔNG HỢP KINH PHÍ")

    ws2.merge_cells("A1:C1")
    cell = ws2["A1"]
    cell.value = "TỔNG HỢP KINH PHÍ XÂY DỰNG"
    cell.font = title_font
    cell.alignment = Alignment(horizontal="center")

    ws2.merge_cells("A2:C2")
    cell = ws2["A2"]
    cell.value = f"Công trình: {project.get('name', '')}"
    cell.font = Font(bold=True, size=12)
    cell.alignment = Alignment(horizontal="center")

    # Summary table
    summary_headers = ["Khoản mục", "Ký hiệu", "Giá trị (đồng)"]
    for col_idx, h in enumerate(summary_headers, 1):
        cell = ws2.cell(row=4, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border
        cell.alignment = Alignment(horizontal="center")

    ws2.column_dimensions["A"].width = 40
    ws2.column_dimensions["B"].width = 12
    ws2.column_dimensions["C"].width = 22

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
            f"Chi phí chung ({summary.get('chi_phi_chung_pct', 6.5)}% × T)",
            "C",
            summary.get("c", 0),
        ),
        (
            f"Thu nhập chịu thuế tính trước ({summary.get('thu_nhap_tt_pct', 5.5)}% × (T+C))",
            "TL",
            summary.get("tl", 0),
        ),
        ("Giá trị dự toán xây dựng trước thuế (G = T + C + TL)", "G", summary.get("g", 0)),
        (
            f"Thuế GTGT ({summary.get('vat_pct', 10)}% × G)",
            "GTGT",
            summary.get("gtgt", 0),
        ),
        (
            f"Chi phí nhà tạm ({summary.get('nha_tam_pct', 1)}% × G)",
            "NT",
            summary.get("nha_tam", 0),
        ),
        ("GIÁ TRỊ DỰ TOÁN XÂY DỰNG SAU THUẾ", "GXD", summary.get("gxd", 0)),
    ]

    for row_idx, (label, symbol, value) in enumerate(summary_rows, 5):
        cell_a = ws2.cell(row=row_idx, column=1, value=label)
        cell_b = ws2.cell(row=row_idx, column=2, value=symbol)
        cell_c = ws2.cell(row=row_idx, column=3, value=value)
        cell_a.border = thin_border
        cell_b.border = thin_border
        cell_b.alignment = Alignment(horizontal="center")
        cell_c.border = thin_border
        cell_c.number_format = number_format
        cell_c.alignment = Alignment(horizontal="right")

        # Bold for totals
        if symbol in ("T", "G", "GXD"):
            cell_a.font = header_font
            cell_b.font = header_font
            cell_c.font = header_font

    # Footer
    last_row = 5 + len(summary_rows) + 1
    ws2.cell(row=last_row, column=3, value=f"Ngày xuất: {datetime.now().strftime('%d/%m/%Y')}")

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def generate_pdf(
    project: dict,
    items: list[dict],
    summary: dict,
) -> io.BytesIO:
    """Generate a PDF report with project items and cost summary.

    Uses reportlab with Vietnamese font support.
    """
    vn_font = _register_vn_font()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "VNTitle",
        parent=styles["Title"],
        fontName=vn_font,
        fontSize=14,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "VNSubtitle",
        parent=styles["Normal"],
        fontName=vn_font,
        fontSize=11,
        alignment=1,  # center
        spaceAfter=12,
    )
    normal_style = ParagraphStyle(
        "VNNormal",
        parent=styles["Normal"],
        fontName=vn_font,
        fontSize=8,
    )
    cell_style = ParagraphStyle(
        "VNCell",
        parent=styles["Normal"],
        fontName=vn_font,
        fontSize=7,
        leading=9,
    )

    elements = []

    # Title
    elements.append(Paragraph("BẢNG DỰ TOÁN CHI PHÍ XÂY DỰNG", title_style))
    elements.append(
        Paragraph(f"Công trình: {project.get('name', '')}", subtitle_style)
    )
    if project.get("description"):
        elements.append(Paragraph(project["description"], subtitle_style))
    elements.append(Spacer(1, 6))

    # Items table
    table_data = [
        [
            "STT",
            "Mã hiệu",
            "Tên công việc",
            "ĐVT",
            "KL",
            "ĐG VL",
            "ĐG NC",
            "ĐG MTC",
            "TT VL",
            "TT NC",
            "TT MTC",
            "Thành tiền",
        ]
    ]

    for idx, item in enumerate(items, 1):
        qty = item.get("quantity", 0)
        vlc = item.get("vlc") or 0
        nc = item.get("nc") or 0
        mtc = item.get("mtc") or 0
        tt_vlc = item.get("thanh_tien_vlc") or round(qty * vlc)
        tt_nc = item.get("thanh_tien_nc") or round(qty * nc)
        tt_mtc = item.get("thanh_tien_mtc") or round(qty * mtc)
        tt = item.get("thanh_tien") or (tt_vlc + tt_nc + tt_mtc)

        # Wrap long text in Paragraph
        tcv = item.get("tcv") or ""
        tcv_para = Paragraph(tcv, cell_style)

        table_data.append([
            str(idx),
            item.get("mhdg", ""),
            tcv_para,
            item.get("dvt", ""),
            _fmt_num(qty),
            _fmt_num(vlc),
            _fmt_num(nc),
            _fmt_num(mtc),
            _fmt_num(tt_vlc),
            _fmt_num(tt_nc),
            _fmt_num(tt_mtc),
            _fmt_num(tt),
        ])

    # Totals row
    table_data.append([
        "",
        "",
        Paragraph("<b>TỔNG CỘNG</b>", cell_style),
        "",
        "",
        "",
        "",
        "",
        _fmt_num(summary.get("vlc", 0)),
        _fmt_num(summary.get("nc", 0)),
        _fmt_num(summary.get("mtc", 0)),
        _fmt_num(summary.get("t", 0)),
    ])

    col_widths = [20, 45, 120, 25, 35, 45, 45, 45, 50, 50, 50, 55]

    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), vn_font),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("FONTNAME", (0, 0), (-1, 0), vn_font),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9E1F2")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("ALIGN", (0, 1), (0, -1), "CENTER"),  # STT
                ("ALIGN", (4, 1), (-1, -1), "RIGHT"),  # numbers
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                # Bold last row
                ("FONTNAME", (0, -1), (-1, -1), vn_font),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F2F2F2")),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 16))

    # Cost summary section
    elements.append(Paragraph("TỔNG HỢP KINH PHÍ XÂY DỰNG", title_style))
    elements.append(Spacer(1, 6))

    summary_data = [
        ["Khoản mục", "Ký hiệu", "Giá trị (đồng)"],
        ["Chi phí vật liệu", "VLC", _fmt_num(summary.get("vlc", 0))],
        ["Chi phí nhân công", "NC", _fmt_num(summary.get("nc", 0))],
        ["Chi phí máy thi công", "MTC", _fmt_num(summary.get("mtc", 0))],
        [
            f"Trực tiếp phí khác ({summary.get('truc_tiep_khac_pct', 2.5)}%)",
            "TTPK",
            _fmt_num(summary.get("truc_tiep_khac", 0)),
        ],
        ["Chi phí trực tiếp (T = VLC + NC + MTC + TTPK)", "T", _fmt_num(summary.get("t", 0))],
        [
            f"Chi phí chung ({summary.get('chi_phi_chung_pct', 6.5)}% x T)",
            "C",
            _fmt_num(summary.get("c", 0)),
        ],
        [
            f"Thu nhập chịu thuế tính trước ({summary.get('thu_nhap_tt_pct', 5.5)}% x (T+C))",
            "TL",
            _fmt_num(summary.get("tl", 0)),
        ],
        ["Giá trị dự toán XD trước thuế (G = T + C + TL)", "G", _fmt_num(summary.get("g", 0))],
        [
            f"Thuế GTGT ({summary.get('vat_pct', 10)}% x G)",
            "GTGT",
            _fmt_num(summary.get("gtgt", 0)),
        ],
        [
            f"Chi phí nhà tạm ({summary.get('nha_tam_pct', 1)}% x G)",
            "NT",
            _fmt_num(summary.get("nha_tam", 0)),
        ],
        [
            Paragraph("<b>GIÁ TRỊ DỰ TOÁN XÂY DỰNG SAU THUẾ</b>", cell_style),
            "GXD",
            _fmt_num(summary.get("gxd", 0)),
        ],
    ]

    summary_table = Table(summary_data, colWidths=[250, 50, 120])
    summary_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), vn_font),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9E1F2")),
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ("ALIGN", (2, 0), (2, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                # Bold for T, G, GXD rows
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E2EFDA")),
            ]
        )
    )
    elements.append(summary_table)
    elements.append(Spacer(1, 12))
    elements.append(
        Paragraph(
            f"Ngày xuất: {datetime.now().strftime('%d/%m/%Y')}",
            normal_style,
        )
    )

    doc.build(elements)
    buf.seek(0)
    return buf


def generate_tmdt_excel(project: dict, tmdt_data: dict) -> io.BytesIO:
    """Generate an Excel workbook for TMDT (Tổng mức đầu tư) report."""
    wb = Workbook()
    ws = wb.active
    ws.title = "TỔNG MỨC ĐẦU TƯ"

    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )
    header_font = Font(bold=True, size=11)
    title_font = Font(bold=True, size=14)
    header_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    subtotal_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
    number_format = "#,##0"

    ws.merge_cells("A1:D1")
    cell = ws["A1"]
    cell.value = "TỔNG MỨC ĐẦU TƯ"
    cell.font = title_font
    cell.alignment = Alignment(horizontal="center")

    ws.merge_cells("A2:D2")
    cell = ws["A2"]
    cell.value = f"Công trình: {project.get('name', '')}"
    cell.font = Font(bold=True, size=12)
    cell.alignment = Alignment(horizontal="center")

    headers = ["STT", "Khoản mục chi phí", "Cách tính", "Thành tiền (đồng)"]
    widths = [8, 45, 20, 22]
    for col_idx, (h, w) in enumerate(zip(headers, widths), 1):
        cell = ws.cell(row=4, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(col_idx)].width = w

    row = 5
    stt = 0

    # G_XD row
    stt += 1
    for col, val in enumerate([stt, "Chi phí xây dựng (GXD)", "Từ dự toán", tmdt_data["g_xd"]], 1):
        c = ws.cell(row=row, column=col, value=val)
        c.border = thin_border
        c.font = header_font
        if col == 4:
            c.number_format = number_format
            c.alignment = Alignment(horizontal="right")
    row += 1

    # Each category
    for cat_data in tmdt_data.get("categories", []):
        stt += 1
        # Category header
        for col, val in enumerate([stt, cat_data["label"], "", cat_data["subtotal"]], 1):
            c = ws.cell(row=row, column=col, value=val)
            c.border = thin_border
            c.font = header_font
            if col == 4:
                c.number_format = number_format
                c.alignment = Alignment(horizontal="right")
        row += 1

        # Items
        for item in cat_data.get("items", []):
            calc_desc = ""
            if item["calc_type"] == "percent" and item.get("percent_value") is not None:
                base_label = "tổng trước DP" if cat_data["category"] == "du_phong" else "GXD"
                calc_desc = f"{item['percent_value']}% x {base_label}"
            else:
                calc_desc = "Cố định"
            for col, val in enumerate(["", f"  - {item['name']}", calc_desc, item["amount"]], 1):
                c = ws.cell(row=row, column=col, value=val)
                c.border = thin_border
                if col == 4:
                    c.number_format = number_format
                    c.alignment = Alignment(horizontal="right")
            row += 1

    # Subtotal before DP
    row += 1
    for col, val in enumerate(["", "Tổng trước dự phòng", "", tmdt_data["subtotal_before_dp"]], 1):
        c = ws.cell(row=row, column=col, value=val)
        c.border = thin_border
        c.font = header_font
        c.fill = subtotal_fill
        if col == 4:
            c.number_format = number_format
            c.alignment = Alignment(horizontal="right")
    row += 1

    # TMDT total
    for col, val in enumerate(["", "TỔNG MỨC ĐẦU TƯ (TMĐT)", "", tmdt_data["tmdt"]], 1):
        c = ws.cell(row=row, column=col, value=val)
        c.border = thin_border
        c.font = Font(bold=True, size=12)
        c.fill = subtotal_fill
        if col == 4:
            c.number_format = number_format
            c.alignment = Alignment(horizontal="right")
    row += 2

    ws.cell(row=row, column=4, value=f"Ngày xuất: {datetime.now().strftime('%d/%m/%Y')}")

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
