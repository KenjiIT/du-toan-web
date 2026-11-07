"""Service cho tra cứu hệ số giá nhân công và giá ca máy theo vùng."""

from sqlalchemy.orm import Session

from app.models.nhan_cong import GiaCaMayVung, GiaNhanCong


def get_available_regions(db: Session) -> list[dict]:
    """Trả về danh sách các vùng có sẵn từ cả hai bảng gia_nhan_cong và gia_ca_may_vung."""
    labor_regions = (
        db.query(GiaNhanCong.region, GiaNhanCong.decision_ref)
        .distinct()
        .all()
    )
    machine_regions = (
        db.query(GiaCaMayVung.region, GiaCaMayVung.zone, GiaCaMayVung.decision_ref)
        .distinct()
        .all()
    )

    region_map: dict[str, dict] = {}
    for row in labor_regions:
        region = row.region
        if region not in region_map:
            region_map[region] = {"region": region, "zones": set(), "refs": set()}
        region_map[region]["zones"].update(["I", "II"])
        if row.decision_ref:
            region_map[region]["refs"].add(row.decision_ref)

    for row in machine_regions:
        region = row.region
        if region not in region_map:
            region_map[region] = {"region": region, "zones": set(), "refs": set()}
        if row.zone:
            region_map[region]["zones"].add(row.zone)
        if row.decision_ref:
            region_map[region]["refs"].add(row.decision_ref)

    return [
        {
            "region": v["region"],
            "zones": sorted(v["zones"]),
            "decision_refs": sorted(v["refs"]),
        }
        for v in sorted(region_map.values(), key=lambda x: x["region"])
    ]


def get_labor_prices(
    db: Session, region: str, q: str | None = None, page: int = 1, limit: int = 20
) -> dict:
    """Trả về giá nhân công cho một vùng, có pagination và search."""
    base = db.query(GiaNhanCong).filter(
        GiaNhanCong.region == region,
        GiaNhanCong.ma_nc != "SHNC",
        GiaNhanCong.khu_vuc_i.isnot(None),
    )
    if q:
        pattern = f"%{q}%"
        base = base.filter(
            (GiaNhanCong.ma_nc.ilike(pattern)) | (GiaNhanCong.nhom.ilike(pattern))
        )

    total = base.count()
    decision_ref = None
    first = base.first()
    if first:
        decision_ref = first.decision_ref

    rows = base.order_by(GiaNhanCong.ma_nc).offset((page - 1) * limit).limit(limit).all()

    items = [
        {
            "ma_nc": r.ma_nc or "",
            "nhom": r.nhom or "",
            "khu_vuc_i": r.khu_vuc_i or 0,
            "khu_vuc_ii": r.khu_vuc_ii or 0,
        }
        for r in rows
    ]
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "region": region,
        "decision_ref": decision_ref,
    }


def get_machine_prices(
    db: Session, region: str, zone: str, q: str | None = None, page: int = 1, limit: int = 20
) -> dict:
    """Trả về giá ca máy cho một vùng và khu vực, có pagination và search."""
    base = db.query(GiaCaMayVung).filter(
        GiaCaMayVung.region == region,
        GiaCaMayVung.zone == zone,
    )
    if q:
        pattern = f"%{q}%"
        base = base.filter(
            (GiaCaMayVung.mh.ilike(pattern)) | (GiaCaMayVung.lm_tb.ilike(pattern))
        )

    total = base.count()
    decision_ref = None
    first = base.first()
    if first:
        decision_ref = first.decision_ref

    rows = base.order_by(GiaCaMayVung.mh).offset((page - 1) * limit).limit(limit).all()

    items = [
        {
            "mh": r.mh or "",
            "lm_tb": r.lm_tb or "",
            "gcm": r.gcm or 0,
            "cpkh": r.cpkh or 0,
            "cpsc": r.cpsc or 0,
            "cpk": r.cpk or 0,
            "cpnl": r.cpnl or 0,
            "cptl": r.cptl or 0,
        }
        for r in rows
    ]
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "region": region,
        "zone": zone,
        "decision_ref": decision_ref,
    }
