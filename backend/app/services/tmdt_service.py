# -*- coding: utf-8 -*-
"""TMDT (Tổng mức đầu tư) calculation service."""

from sqlalchemy.orm import Session

from app.models.project import ProjectOtherCost
from app.services.cost_summary import calculate_cost_summary_for_project

CATEGORY_LABELS = {
    "thiet_bi": "Chi phí thiết bị",
    "tu_van": "Chi phí tư vấn",
    "qlda": "Chi phí quản lý dự án",
    "khac": "Chi phí khác",
    "du_phong": "Chi phí dự phòng",
}

CATEGORY_ORDER = ["thiet_bi", "tu_van", "qlda", "khac", "du_phong"]

DEFAULTS = [
    {"category": "tu_van", "name": "Khảo sát xây dựng", "calc_type": "percent", "percent_value": 1.5, "sort_order": 0},
    {"category": "tu_van", "name": "Thiết kế kỹ thuật", "calc_type": "percent", "percent_value": 3.0, "sort_order": 1},
    {"category": "tu_van", "name": "Thẩm tra thiết kế", "calc_type": "percent", "percent_value": 0.2, "sort_order": 2},
    {"category": "tu_van", "name": "Lập dự toán", "calc_type": "percent", "percent_value": 0.4, "sort_order": 3},
    {"category": "tu_van", "name": "Thẩm tra dự toán", "calc_type": "percent", "percent_value": 0.15, "sort_order": 4},
    {"category": "tu_van", "name": "Giám sát thi công XD", "calc_type": "percent", "percent_value": 2.5, "sort_order": 5},
    {"category": "qlda", "name": "Quản lý dự án", "calc_type": "percent", "percent_value": 2.5, "sort_order": 0},
    {"category": "khac", "name": "Bảo hiểm công trình", "calc_type": "percent", "percent_value": 0.5, "sort_order": 0},
    {"category": "khac", "name": "Kiểm toán", "calc_type": "percent", "percent_value": 0.15, "sort_order": 1},
    {"category": "du_phong", "name": "Dự phòng khối lượng phát sinh", "calc_type": "percent", "percent_value": 5.0, "sort_order": 0},
    {"category": "du_phong", "name": "Dự phòng trượt giá", "calc_type": "percent", "percent_value": 5.0, "sort_order": 1},
]


def init_default_costs(db: Session, project_id: int) -> list[ProjectOtherCost]:
    """Create default other cost items for a project. Skips if items already exist."""
    existing = db.query(ProjectOtherCost).filter(
        ProjectOtherCost.project_id == project_id
    ).count()
    if existing > 0:
        return []

    created = []
    for d in DEFAULTS:
        cost = ProjectOtherCost(project_id=project_id, **d)
        db.add(cost)
        created.append(cost)
    db.flush()
    return created


def calculate_tmdt(db: Session, project_id: int) -> dict:
    """Calculate full TMDT (Tổng mức đầu tư) for a project."""
    summary = calculate_cost_summary_for_project(db, project_id)
    g_xd = summary["gxd"]

    costs = db.query(ProjectOtherCost).filter(
        ProjectOtherCost.project_id == project_id
    ).order_by(ProjectOtherCost.sort_order).all()

    # Group by category
    by_cat: dict[str, list] = {}
    for c in costs:
        by_cat.setdefault(c.category, []).append(c)

    # Calculate amounts for non-du_phong categories first
    categories = []
    cat_totals = {}

    for cat in CATEGORY_ORDER:
        if cat == "du_phong":
            continue  # handle after subtotal
        items_list = by_cat.get(cat, [])
        cat_items = []
        cat_subtotal = 0
        for item in items_list:
            if item.calc_type == "percent" and item.percent_value is not None:
                amount = round(g_xd * item.percent_value / 100)
            elif item.calc_type == "fixed" and item.fixed_value is not None:
                amount = round(item.fixed_value)
            else:
                amount = 0
            cat_items.append({
                "id": item.id,
                "name": item.name,
                "calc_type": item.calc_type,
                "percent_value": item.percent_value,
                "fixed_value": item.fixed_value,
                "amount": amount,
            })
            cat_subtotal += amount

        categories.append({
            "category": cat,
            "label": CATEGORY_LABELS.get(cat, cat),
            "items": cat_items,
            "subtotal": cat_subtotal,
        })
        cat_totals[cat] = cat_subtotal

    g_tb = cat_totals.get("thiet_bi", 0)
    g_tv = cat_totals.get("tu_van", 0)
    g_qlda = cat_totals.get("qlda", 0)
    g_k = cat_totals.get("khac", 0)

    subtotal_before_dp = g_xd + g_tb + g_tv + g_qlda + g_k

    # Du phong: percent is on subtotal_before_dp, not g_xd
    dp_items_list = by_cat.get("du_phong", [])
    dp_cat_items = []
    dp_subtotal = 0
    for item in dp_items_list:
        if item.calc_type == "percent" and item.percent_value is not None:
            amount = round(subtotal_before_dp * item.percent_value / 100)
        elif item.calc_type == "fixed" and item.fixed_value is not None:
            amount = round(item.fixed_value)
        else:
            amount = 0
        dp_cat_items.append({
            "id": item.id,
            "name": item.name,
            "calc_type": item.calc_type,
            "percent_value": item.percent_value,
            "fixed_value": item.fixed_value,
            "amount": amount,
        })
        dp_subtotal += amount

    categories.append({
        "category": "du_phong",
        "label": CATEGORY_LABELS["du_phong"],
        "items": dp_cat_items,
        "subtotal": dp_subtotal,
    })

    g_dp = dp_subtotal
    tmdt = subtotal_before_dp + g_dp

    return {
        "g_xd": g_xd,
        "categories": categories,
        "g_tb": g_tb,
        "g_tv": g_tv,
        "g_qlda": g_qlda,
        "g_k": g_k,
        "subtotal_before_dp": subtotal_before_dp,
        "g_dp": g_dp,
        "tmdt": tmdt,
    }
