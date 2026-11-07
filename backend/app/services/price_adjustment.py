# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session

from app.models.don_gia import DonGia, TuDienVatTu
from app.models.project import Project, ProjectItem, ProjectSettings
from app.services.price_calculator import _find_vt, _get_first_resource_group


def calculate_price_adjustment(
    db: Session, project_id: int, source_market: str = "HoChiMinh2023"
) -> dict:
    """Calculate price adjustment (bù giá vật tư) for a project."""
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

    items = db.query(ProjectItem).filter(ProjectItem.project_id == project_id).all()

    # Aggregate materials across all items
    material_agg: dict[str, dict] = {}  # msvt -> aggregated info
    items_detail = []

    for item in items:
        qty = item.quantity or 0
        if qty == 0:
            continue

        # Get don_gia to find mhdm
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

        dm_rows = _get_first_resource_group(db, dg.mhdm, reg, dbt)

        item_materials = []
        item_bu_gia = 0.0

        for dm in dm_rows:
            msvt = dm.msvt
            if not msvt or not msvt.startswith("V"):
                continue

            hp = dm.hao_phi or 0
            if hp == 0:
                continue

            # Get norm price
            vt_norm = _find_vt(db, msvt, reg, "norm")
            gia_dm = (vt_norm.gia_goc or 0) if vt_norm else 0
            tvt = vt_norm.tvt if vt_norm else None
            dvt = vt_norm.dvt if vt_norm else None

            # Get market price
            vt_market = _find_vt(db, msvt, reg, source_market)
            gia_tt = (vt_market.gia_goc or 0) if vt_market else 0

            # Use market vt for name/unit if norm didn't have it
            if not tvt and vt_market:
                tvt = vt_market.tvt
            if not dvt and vt_market:
                dvt = vt_market.dvt

            chenh_lech_dv = gia_tt - gia_dm
            chenh_lech_tt = round(hp * chenh_lech_dv * qty)

            mat_info = {
                "msvt": msvt,
                "tvt": tvt,
                "dvt": dvt,
                "hao_phi": hp,
                "gia_dm": gia_dm,
                "gia_tt": gia_tt,
                "chenh_lech_dv": chenh_lech_dv,
                "chenh_lech_tt": round(hp * chenh_lech_dv * qty),
            }
            item_materials.append(mat_info)
            item_bu_gia += chenh_lech_tt

            # Aggregate
            if msvt not in material_agg:
                material_agg[msvt] = {
                    "msvt": msvt,
                    "tvt": tvt,
                    "dvt": dvt,
                    "total_hao_phi": 0.0,
                    "gia_dm": gia_dm,
                    "gia_tt": gia_tt,
                    "chenh_lech_dv": chenh_lech_dv,
                    "chenh_lech_tt": 0.0,
                }
            material_agg[msvt]["total_hao_phi"] += hp * qty
            material_agg[msvt]["chenh_lech_tt"] += hp * chenh_lech_dv * qty

        if item_materials:
            items_detail.append(
                {
                    "mhdg": item.mhdg,
                    "tcv": item.tcv,
                    "quantity": qty,
                    "materials": item_materials,
                    "bu_gia_item": round(item_bu_gia),
                }
            )

    # Finalize aggregated materials
    materials = []
    for mat in material_agg.values():
        mat["total_hao_phi"] = round(mat["total_hao_phi"], 4)
        mat["chenh_lech_tt"] = round(mat["chenh_lech_tt"])
        materials.append(mat)

    # Sort by absolute chenh_lech_tt descending
    materials.sort(key=lambda m: abs(m["chenh_lech_tt"]), reverse=True)

    total_bu_gia = round(sum(m["chenh_lech_tt"] for m in materials))

    return {
        "source_norm": "norm",
        "source_market": source_market,
        "materials": materials,
        "total_bu_gia": total_bu_gia,
        "items_detail": items_detail,
    }


def get_available_sources(db: Session) -> list[str]:
    """Return distinct market sources (not 'norm') from tu_dien_vat_tu."""
    rows = (
        db.query(TuDienVatTu.source)
        .filter(TuDienVatTu.source != "norm", TuDienVatTu.source.isnot(None))
        .distinct()
        .order_by(TuDienVatTu.source)
        .all()
    )
    return [r[0] for r in rows]
