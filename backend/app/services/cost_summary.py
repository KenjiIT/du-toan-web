# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session

from app.models.project import ProjectItem, ProjectSettings
from app.services.price_calculator import calculate_unit_price

OVERHEAD_RATES = {
    "XD": {"c_rate": 0.065, "tl_rate": 0.055},
    "LD": {"c_rate": 0.055, "tl_rate": 0.055},
    "SC": {"c_rate": 0.065, "tl_rate": 0.055},
}
VAT_RATE = 0.10

SECTION_NAMES = {
    "XD": "Xây dựng",
    "LD": "Lắp đặt",
    "SC": "Sửa chữa",
    "KS": "Khảo sát",
}

DEFAULT_SECTION_RATES = {
    "XD": {"chi_phi_chung_pct": 6.5, "thu_nhap_tt_pct": 5.5},
    "LD": {"chi_phi_chung_pct": 5.5, "thu_nhap_tt_pct": 5.5},
    "SC": {"chi_phi_chung_pct": 5.5, "thu_nhap_tt_pct": 5.5},
    "KS": {"chi_phi_chung_pct": 4.0, "thu_nhap_tt_pct": 5.5},
}


def detect_cost_type(mhdg: str) -> str:
    """Detect cost_type from mhdg prefix."""
    prefix = mhdg[:2].upper() if len(mhdg) >= 2 else ""
    if prefix in ("SA", "SB", "SC", "SD", "SE", "SF"):
        return "SC"
    if prefix in ("BA", "BB", "BC", "BD"):
        return "LD"
    if prefix in ("CA", "CB", "CC", "CD", "CE", "CF", "CG", "CH", "CI", "CK"):
        return "KS"
    return "XD"  # AA-AN, TT, and anything else


def calculate_project_summary(
    db: Session,
    items: list[dict],
    regulation_code: str = "TT12-2021",
    db_type: str = "XD+LD+SC",
    source: str = "norm",
    cost_type: str = "XD",
) -> dict:
    """Calculate cost summary from a list of item dicts (standalone, no project)."""
    rates = OVERHEAD_RATES.get(cost_type, OVERHEAD_RATES["XD"])
    c_rate = rates["c_rate"]
    tl_rate = rates["tl_rate"]

    total_vl = 0.0
    total_nc = 0.0
    total_mtc = 0.0
    item_results = []

    for entry in items:
        mhdg = entry["mhdg"]
        qty = entry.get("quantity", 1)
        calc = calculate_unit_price(db, mhdg, regulation_code, db_type, source)
        if "error" in calc:
            item_results.append({"mhdg": mhdg, "error": calc["error"]})
            continue

        vl = calc["vlc"] * qty
        nc = calc["nc"] * qty
        mtc = calc["mtc"] * qty
        total_vl += vl
        total_nc += nc
        total_mtc += mtc

        item_results.append({
            "mhdg": mhdg,
            "tcv": calc["tcv"],
            "dvt": calc["dvt"],
            "quantity": qty,
            "don_gia_vlc": calc["vlc"],
            "don_gia_nc": calc["nc"],
            "don_gia_mtc": calc["mtc"],
            "don_gia_total": calc["total"],
            "thanh_tien_vlc": round(vl),
            "thanh_tien_nc": round(nc),
            "thanh_tien_mtc": round(mtc),
            "thanh_tien": round(vl + nc + mtc),
        })

    t = total_vl + total_nc + total_mtc
    c = t * c_rate
    tl = (t + c) * tl_rate
    g = t + c + tl
    gtgt = g * VAT_RATE
    gxd = g + gtgt

    return {
        "vl": round(total_vl),
        "nc": round(total_nc),
        "mtc": round(total_mtc),
        "tt": 0,
        "t": round(t),
        "c_rate": c_rate,
        "c": round(c),
        "tl_rate": tl_rate,
        "tl": round(tl),
        "g": round(g),
        "gtgt_rate": VAT_RATE,
        "gtgt": round(gtgt),
        "gxd": round(gxd),
        "items": item_results,
    }


def calculate_section_summary(items: list, settings, section=None, *, estimate_type: str = "new") -> dict:
    """Calculate cost summary for a set of items with optional section-level rate overrides.

    ``settings`` is a ProjectSettings ORM object (or a bare default instance).
    ``section`` is an optional ProjectSection ORM object whose per-section rates
    override the project defaults.
    ``estimate_type`` controls whether K repair coefficients are applied.
    """
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

    total_vlc = round(total_vlc)
    total_nc = round(total_nc)
    total_mtc = round(total_mtc)

    # Apply K coefficients for repair/renovation estimates
    k_vlc = getattr(settings, "k_vlc", None)
    k_nc = getattr(settings, "k_nc", None)
    k_mtc = getattr(settings, "k_mtc", None)
    if estimate_type == "repair":
        if k_vlc is not None:
            total_vlc = round(total_vlc * k_vlc)
        if k_nc is not None:
            total_nc = round(total_nc * k_nc)
        if k_mtc is not None:
            total_mtc = round(total_mtc * k_mtc)

    # Determine rates: section override > default for cost_type > project settings
    if section and section.chi_phi_chung_pct is not None:
        cpc = section.chi_phi_chung_pct
    elif section:
        defaults = DEFAULT_SECTION_RATES.get(section.cost_type, DEFAULT_SECTION_RATES["XD"])
        cpc = defaults["chi_phi_chung_pct"]
    else:
        cpc = getattr(settings, "chi_phi_chung_pct", None) or 6.5

    if section and section.thu_nhap_tt_pct is not None:
        tnp = section.thu_nhap_tt_pct
    elif section:
        defaults = DEFAULT_SECTION_RATES.get(section.cost_type, DEFAULT_SECTION_RATES["XD"])
        tnp = defaults["thu_nhap_tt_pct"]
    else:
        tnp = getattr(settings, "thu_nhap_tt_pct", None) or 5.5

    truc_tiep_khac_pct = getattr(settings, "truc_tiep_khac_pct", None) or 0
    vat_pct = getattr(settings, "vat_pct", None) or 10.0
    nha_tam_pct = getattr(settings, "nha_tam_pct", None) or 1.0

    truc_tiep_khac = round((total_vlc + total_nc + total_mtc) * truc_tiep_khac_pct / 100)
    t = total_vlc + total_nc + total_mtc + truc_tiep_khac
    c = round(t * cpc / 100)
    tl = round((t + c) * tnp / 100)
    g = t + c + tl
    gtgt = round(g * vat_pct / 100)
    nha_tam = round(g * nha_tam_pct / 100)
    gxd = g + gtgt + nha_tam

    return {
        "vlc": total_vlc,
        "nc": total_nc,
        "mtc": total_mtc,
        "truc_tiep_khac": truc_tiep_khac,
        "t": t,
        "c": c,
        "tl": tl,
        "g": g,
        "gtgt": gtgt,
        "nha_tam": nha_tam,
        "gxd": gxd,
        "chi_phi_chung_pct": cpc,
        "thu_nhap_tt_pct": tnp,
        "vat_pct": vat_pct,
        "nha_tam_pct": nha_tam_pct,
        "truc_tiep_khac_pct": truc_tiep_khac_pct or 2.5,
    }


def calculate_cost_summary_for_project(db: Session, project_id: int) -> dict:
    """Calculate the full cost summary for a saved project using the GXD formula.

    T  = VLC + NC + MTC + TT (truc tiep khac)
    C  = T * chi_phi_chung_pct%
    TL = (T + C) * thu_nhap_tt_pct%
    G  = T + C + TL
    GTGT = G * vat_pct%
    Nha tam = G * nha_tam_pct%
    GXD = G + GTGT + Nha tam

    When estimate_type == "repair", K coefficients are applied to VLC/NC/MTC.
    """
    from app.models.project import Project as ProjectModel

    settings = db.query(ProjectSettings).filter(ProjectSettings.project_id == project_id).first()
    if not settings:
        settings = ProjectSettings()

    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    estimate_type = getattr(project, "estimate_type", None) or "new"

    items = db.query(ProjectItem).filter(ProjectItem.project_id == project_id).all()

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

    total_vlc = round(total_vlc)
    total_nc = round(total_nc)
    total_mtc = round(total_mtc)

    # Apply K coefficients for repair/renovation estimates
    k_vlc = settings.k_vlc
    k_nc = settings.k_nc
    k_mtc = settings.k_mtc
    if estimate_type == "repair":
        if k_vlc is not None:
            total_vlc = round(total_vlc * k_vlc)
        if k_nc is not None:
            total_nc = round(total_nc * k_nc)
        if k_mtc is not None:
            total_mtc = round(total_mtc * k_mtc)

    truc_tiep_khac = round((total_vlc + total_nc + total_mtc) * (settings.truc_tiep_khac_pct or 0) / 100)
    t = total_vlc + total_nc + total_mtc + truc_tiep_khac
    c = round(t * (settings.chi_phi_chung_pct or 0) / 100)
    tl = round((t + c) * (settings.thu_nhap_tt_pct or 0) / 100)
    g = t + c + tl
    gtgt = round(g * (settings.vat_pct or 0) / 100)
    nha_tam = round(g * (settings.nha_tam_pct or 0) / 100)
    gxd = g + gtgt + nha_tam

    return {
        "vlc": total_vlc,
        "nc": total_nc,
        "mtc": total_mtc,
        "truc_tiep_khac": truc_tiep_khac,
        "t": t,
        "c": c,
        "tl": tl,
        "g": g,
        "gtgt": gtgt,
        "nha_tam": nha_tam,
        "gxd": gxd,
        "chi_phi_chung_pct": settings.chi_phi_chung_pct or 6.5,
        "thu_nhap_tt_pct": settings.thu_nhap_tt_pct or 5.5,
        "vat_pct": settings.vat_pct or 10.0,
        "nha_tam_pct": settings.nha_tam_pct or 1.0,
        "truc_tiep_khac_pct": settings.truc_tiep_khac_pct or 2.5,
        "estimate_type": estimate_type,
        "k_vlc": k_vlc,
        "k_nc": k_nc,
        "k_mtc": k_mtc,
    }


def calculate_cost_summary_by_sections(db: Session, project_id: int) -> dict:
    """Calculate cost summary grouped by sections."""
    from app.models.project import ProjectSection

    settings = db.query(ProjectSettings).filter(ProjectSettings.project_id == project_id).first()
    if not settings:
        settings = ProjectSettings()

    sections = db.query(ProjectSection).filter(
        ProjectSection.project_id == project_id
    ).order_by(ProjectSection.sort_order).all()

    if not sections:
        # No sections - fallback to flat calculation
        return calculate_cost_summary_for_project(db, project_id)

    from app.models.project import Project as ProjectModel
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    estimate_type = getattr(project, "estimate_type", None) or "new"

    section_summaries = []
    total_gxd = 0
    for section in sections:
        section_items = db.query(ProjectItem).filter(
            ProjectItem.section_id == section.id
        ).all()
        summary = calculate_section_summary(section_items, settings, section, estimate_type=estimate_type)
        total_gxd += summary["gxd"]
        section_summaries.append({
            "section_id": section.id,
            "cost_type": section.cost_type,
            "name": section.name,
            **summary,
        })

    # Also handle unassigned items
    unassigned = db.query(ProjectItem).filter(
        ProjectItem.project_id == project_id,
        ProjectItem.section_id == None,  # noqa: E711
    ).all()
    if unassigned:
        unsummary = calculate_section_summary(unassigned, settings, estimate_type=estimate_type)
        total_gxd += unsummary["gxd"]
        section_summaries.append({
            "section_id": None,
            "cost_type": None,
            "name": "Chưa phân hạng mục",
            **unsummary,
        })

    # Overall summary = sum of all sections
    overall = calculate_cost_summary_for_project(db, project_id)
    overall["total_gxd_by_sections"] = total_gxd
    overall["sections"] = section_summaries

    return overall
