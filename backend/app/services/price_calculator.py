from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.don_gia import DinhMuc, DonGia, GiaCaMay, PhuLucVua, TuDienVatTu

MORTAR_PLACEHOLDER_CODES = {"V19999", "V10875"}


def _find_vt(db, msvt, regulation_code, source):
    """Find tu_dien_vat_tu with price, trying exact source → LIKE → norm."""
    base = db.query(TuDienVatTu).filter(
        TuDienVatTu.msvt == msvt,
        TuDienVatTu.regulation_code == regulation_code,
    )
    vt = (
        base.filter(TuDienVatTu.source == source)
        .filter(TuDienVatTu.gia_goc.isnot(None))
        .first()
    )
    if vt:
        return vt
    if source != "norm":
        base_prefix = source.rstrip("0123456789")
        vt = (
            base.filter(TuDienVatTu.source.like(f"{source}%"))
            .filter(TuDienVatTu.gia_goc.isnot(None))
            .first()
        )
        if vt:
            return vt
        vt = (
            base.filter(TuDienVatTu.source == "norm")
            .filter(TuDienVatTu.gia_goc.isnot(None))
            .first()
        )
        if vt:
            return vt
    return base.filter(TuDienVatTu.gia_goc.isnot(None)).first()


def _get_resource_price(
    db: Session,
    msvt: str,
    regulation_code: str,
    db_type: str,
    source: str,
) -> tuple[float, str | None, str | None]:
    """Return (price, name, unit) for a resource code."""
    vt = _find_vt(db, msvt, regulation_code, source)
    if vt:
        return (vt.gia_goc or 0, vt.tvt, vt.dvt)
    if msvt.startswith("M"):
        gcm = (
            db.query(GiaCaMay)
            .filter(
                GiaCaMay.mh == msvt,
                GiaCaMay.regulation_code == regulation_code,
                GiaCaMay.source == source,
                GiaCaMay.gcm.isnot(None),
            )
            .first()
        )
        if not gcm and source != "norm":
            gcm = (
                db.query(GiaCaMay)
                .filter(
                    GiaCaMay.mh == msvt,
                    GiaCaMay.regulation_code == regulation_code,
                    GiaCaMay.source.like(f"{source}%"),
                    GiaCaMay.gcm.isnot(None),
                )
                .first()
            )
        if not gcm and source != "norm":
            gcm = (
                db.query(GiaCaMay)
                .filter(
                    GiaCaMay.mh == msvt,
                    GiaCaMay.regulation_code == regulation_code,
                    GiaCaMay.source == "norm",
                    GiaCaMay.gcm.isnot(None),
                )
                .first()
            )
        if gcm:
            return (gcm.gcm or 0, gcm.lm_tb, "ca")
    return (0, None, None)


def _resolve_mortar(
    db: Session,
    plv_code: str,
    regulation_code: str,
    db_type: str,
    source: str,
) -> dict | None:
    """Resolve a mortar/concrete recipe (PLV) into material cost per unit."""
    plv = (
        db.query(PhuLucVua)
        .filter(
            PhuLucVua.btm == plv_code,
            PhuLucVua.regulation_code == regulation_code,
            PhuLucVua.db_type == db_type,
        )
        .first()
    )
    if not plv:
        return None

    components = []
    total_cost = 0.0
    slots = [
        (plv.mxm, plv.hpxm, "Xi mang"),
        (plv.cat, plv.hpc, "Cat"),
        (plv.da, plv.hpd, "Da"),
        (plv.vcuc, plv.hpv, "Nuoc"),
    ]
    for i in range(1, 5):
        ma = getattr(plv, f"ma{i}", None)
        hp = getattr(plv, f"hp{i}", None)
        if ma:
            slots.append((ma, hp, f"Phu gia {i}"))

    for mat_code, qty, label in slots:
        if not mat_code or not qty:
            continue
        price, name, dvt = _get_resource_price(
            db, mat_code, regulation_code, db_type, source
        )
        cost = (qty or 0) * price
        total_cost += cost
        components.append({
            "msvt": mat_code,
            "tvt": name or label,
            "dvt": dvt,
            "hao_phi": qty,
            "gia": price,
            "thanh_tien": round(cost),
        })

    return {
        "btm": plv.btm,
        "tg": plv.tg,
        "total_cost": round(total_cost),
        "components": components,
    }


def _get_first_resource_group(
    db: Session,
    mhdm: str,
    regulation_code: str,
    db_type: str,
) -> list:
    """Get the first consistent resource group for a dinh_muc code.

    Multiple .mdb imports created duplicate rows with different code styles
    (NC vs N prefix, M1xx vs M0xxx). Groups are contiguous by ID; a gap
    >1000 in row IDs marks the boundary to the next import batch.
    """
    rows = (
        db.query(DinhMuc)
        .filter(
            DinhMuc.mhdm == mhdm,
            DinhMuc.regulation_code == regulation_code,
            DinhMuc.db_type == db_type,
        )
        .order_by(DinhMuc.id)
        .all()
    )
    if not rows:
        return []

    GAP_THRESHOLD = 1000
    first_group = []
    prev_id = None
    for r in rows:
        if not r.msvt:
            continue
        if prev_id is not None and (r.id - prev_id) > GAP_THRESHOLD:
            break
        first_group.append(r)
        prev_id = r.id
    return first_group


def calculate_unit_price(
    db: Session,
    mhdg: str,
    regulation_code: str = "TT12-2021",
    db_type: str = "XD+LD+SC",
    source: str = "norm",
) -> dict:
    """Calculate the full unit price breakdown for a work item."""
    item = (
        db.query(DonGia)
        .filter(
            DonGia.mhdg == mhdg,
            DonGia.regulation_code == regulation_code,
            DonGia.db_type == db_type,
            DonGia.source == source,
        )
        .first()
    )
    if not item:
        item = (
            db.query(DonGia)
            .filter(
                DonGia.mhdg == mhdg,
                DonGia.regulation_code == regulation_code,
                DonGia.db_type == db_type,
                DonGia.source == "norm",
            )
            .first()
        )
    if not item:
        return {"error": f"Work item {mhdg} not found"}

    dm_rows = _get_first_resource_group(
        db, item.mhdm, regulation_code, db_type
    )

    plv_info = None
    mortar_cost = 0.0
    if item.plv:
        plv_info = _resolve_mortar(
            db, item.plv, regulation_code, db_type, source
        )
        if plv_info:
            mortar_cost = plv_info["total_cost"]

    all_codes = {dm.msvt for dm in dm_rows}
    has_v19999 = "V19999" in all_codes

    total_vlc = 0.0
    total_nc = 0.0
    total_mtc = 0.0
    details = []

    for dm in dm_rows:
        hp = dm.hao_phi or 0

        is_mortar = dm.msvt in MORTAR_PLACEHOLDER_CODES and mortar_cost > 0
        if dm.msvt == "V10875" and has_v19999:
            is_mortar = False

        if is_mortar:
            cost = hp * mortar_cost
            total_vlc += cost
            details.append({
                "msvt": dm.msvt,
                "tvt": plv_info["tg"] if plv_info else "Vua",
                "dvt": "m3",
                "type": "VL",
                "hao_phi": hp,
                "gia": round(mortar_cost),
                "thanh_tien": round(cost),
            })
            continue

        if dm.msvt in MORTAR_PLACEHOLDER_CODES:
            continue

        price, name, dvt = _get_resource_price(
            db, dm.msvt, regulation_code, db_type, source
        )

        if price == 0:
            continue

        cost = hp * price
        if dm.msvt.startswith("V"):
            rtype = "VL"
            total_vlc += cost
        elif dm.msvt.startswith("NC") or dm.msvt.startswith("N"):
            rtype = "NC"
            total_nc += cost
        elif dm.msvt.startswith("M"):
            rtype = "MTC"
            total_mtc += cost
        else:
            rtype = "?"
            total_vlc += cost

        details.append({
            "msvt": dm.msvt,
            "tvt": name,
            "dvt": dvt,
            "type": rtype,
            "hao_phi": hp,
            "gia": round(price),
            "thanh_tien": round(cost),
        })

    return {
        "mhdg": item.mhdg,
        "tcv": item.tcv,
        "dvt": item.dvt,
        "vlc": round(total_vlc),
        "nc": round(total_nc),
        "mtc": round(total_mtc),
        "total": round(total_vlc + total_nc + total_mtc),
        "details": details,
        "phu_luc_vua": plv_info,
    }
