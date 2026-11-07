# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from app.models.project import Project, ProjectItem, ProjectSection


def calculate_settlement(db: Session, project_id: int) -> dict:
    """Calculate settlement comparison for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return {"error": "Project not found"}

    items = db.query(ProjectItem).filter(
        ProjectItem.project_id == project_id
    ).order_by(ProjectItem.sort_order).all()

    sections = db.query(ProjectSection).filter(
        ProjectSection.project_id == project_id
    ).all()
    section_map = {s.id: s.name for s in sections}

    settlement_items = []
    section_summaries = {}
    total_du_toan = 0
    total_thuc_te = 0
    items_with_actual = 0

    for item in items:
        qty = item.quantity or 0
        eff_vlc = item.override_vlc if item.override_vlc is not None else (item.vlc or 0)
        eff_nc = item.override_nc if item.override_nc is not None else (item.nc or 0)
        eff_mtc = item.override_mtc if item.override_mtc is not None else (item.mtc or 0)
        unit_price = eff_vlc + eff_nc + eff_mtc

        thanh_tien_dt = round(qty * unit_price)
        actual_qty = item.actual_quantity
        thanh_tien_tt = round((actual_qty or 0) * unit_price)
        chenh_lech = thanh_tien_tt - thanh_tien_dt

        if actual_qty is not None:
            items_with_actual += 1

        total_du_toan += thanh_tien_dt
        total_thuc_te += thanh_tien_tt

        sec_name = section_map.get(item.section_id) if item.section_id else None

        settlement_items.append({
            "id": item.id,
            "mhdg": item.mhdg,
            "tcv": item.tcv,
            "dvt": item.dvt,
            "quantity": qty,
            "actual_quantity": actual_qty,
            "acceptance_date": item.acceptance_date,
            "acceptance_notes": item.acceptance_notes,
            "unit_price": unit_price,
            "thanh_tien_du_toan": thanh_tien_dt,
            "thanh_tien_thuc_te": thanh_tien_tt,
            "chenh_lech": chenh_lech,
            "section_id": item.section_id,
            "section_name": sec_name,
        })

        # Group by section
        sec_key = item.section_id or 0
        if sec_key not in section_summaries:
            section_summaries[sec_key] = {
                "section_id": item.section_id,
                "section_name": sec_name or "Chua phan hang muc",
                "total_du_toan": 0,
                "total_thuc_te": 0,
                "chenh_lech": 0,
                "item_count": 0,
            }
        section_summaries[sec_key]["total_du_toan"] += thanh_tien_dt
        section_summaries[sec_key]["total_thuc_te"] += thanh_tien_tt
        section_summaries[sec_key]["chenh_lech"] += chenh_lech
        section_summaries[sec_key]["item_count"] += 1

    total_chenh_lech = total_thuc_te - total_du_toan
    pct = (items_with_actual / len(items) * 100) if items else 0

    return {
        "project_id": project_id,
        "project_name": project.name,
        "items": settlement_items,
        "sections": list(section_summaries.values()),
        "total_du_toan": total_du_toan,
        "total_thuc_te": total_thuc_te,
        "total_chenh_lech": total_chenh_lech,
        "pct_hoan_thanh": round(pct, 1),
        "items_with_actual": items_with_actual,
        "total_items": len(items),
    }
