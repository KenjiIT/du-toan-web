from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.don_gia import DinhMuc, DonGia, PhuLucVua, TuDienVatTu
from app.services.price_calculator import calculate_unit_price
from app.schemas.don_gia import (
    ChapterResponse,
    DinhMucResponse,
    DonGiaDetailResponse,
    DonGiaResponse,
    DonGiaSearchResponse,
    PhuLucVuaResponse,
)

router = APIRouter(prefix="/don-gia", tags=["don-gia"])

CHAPTER_NAMES = {
    "AA": "Phát rừng, phát hoang",
    "AB": "Công tác đất",
    "AC": "Công tác đóng cọc",
    "AD": "Công tác làm đường",
    "AE": "Công tác xây",
    "AF": "Công tác bê tông",
    "AG": "Bê tông đúc sẵn",
    "AH": "Công tác gỗ",
    "AI": "Kết cấu thép",
    "AK": "Mái, trần, chống thấm",
    "AL": "Công tác dưới nước",
    "AM": "Bốc xếp, vận chuyển",
    "AN": "Tro xỉ",
    "BA": "Lắp đặt điện",
    "BB": "Lắp đặt ống",
    "BC": "Bảo ôn, cách nhiệt",
    "BD": "Khoan ngầm",
    "SA": "Phá dỡ",
    "SB": "Sửa chữa xây",
    "SE": "Sửa chữa đường",
    "SF": "Sửa chữa mái dốc",
    "TT": "Công tác tạm",
}


@router.get("/chapters", response_model=list[ChapterResponse])
def list_chapters(
    regulation_code: str = Query("TT12-2021"),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(
            func.substr(DonGia.mhdg, 1, 2).label("code"),
            func.count().label("cnt"),
        )
        .filter(DonGia.regulation_code == regulation_code, DonGia.source == "norm")
        .group_by(text("1"))
        .order_by(text("1"))
        .all()
    )
    return [
        ChapterResponse(code=r.code, name=CHAPTER_NAMES.get(r.code, ""), count=r.cnt)
        for r in rows
    ]


@router.get("", response_model=DonGiaSearchResponse)
def search_don_gia(
    q: str | None = None,
    chapter: str | None = None,
    regulation_code: str = Query("TT12-2021"),
    db_type: str = Query("XD+LD+SC"),
    region: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(DonGia).filter(
        DonGia.regulation_code == regulation_code,
        DonGia.db_type == db_type,
    )

    if region:
        query = query.filter(DonGia.source == region)
    else:
        query = query.filter(DonGia.source == "norm")

    if chapter:
        query = query.filter(DonGia.mhdg.like(f"{chapter}%"))

    if q:
        query = query.filter(
            DonGia.mhdg.contains(q) | DonGia.tcv.contains(q) | DonGia.tk.contains(q)
        )

    total = query.count()
    items = query.order_by(DonGia.mhdg).offset((page - 1) * limit).limit(limit).all()

    return DonGiaSearchResponse(
        items=[DonGiaResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{mhdg}", response_model=DonGiaDetailResponse)
def get_don_gia_detail(
    mhdg: str,
    regulation_code: str = Query("TT12-2021"),
    region: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(DonGia).filter(
        DonGia.mhdg == mhdg,
        DonGia.regulation_code == regulation_code,
    )
    if region:
        query = query.filter(DonGia.source == region)
    else:
        query = query.filter(DonGia.source == "norm")

    item = query.first()
    if not item:
        from fastapi import HTTPException
        raise HTTPException(404, f"Work item {mhdg} not found")

    dm_rows = (
        db.query(DinhMuc)
        .filter(
            DinhMuc.mhdm == item.mhdm,
            DinhMuc.regulation_code == regulation_code,
            DinhMuc.db_type == item.db_type,
        )
        .group_by(DinhMuc.msvt)
        .all()
    )

    vt_codes = [r.msvt for r in dm_rows if r.msvt]
    vt_map: dict[str, TuDienVatTu] = {}
    if vt_codes:
        vt_source = region if region else "norm"
        vt_rows = (
            db.query(TuDienVatTu)
            .filter(
                TuDienVatTu.msvt.in_(vt_codes),
                TuDienVatTu.regulation_code == regulation_code,
                TuDienVatTu.source == vt_source,
            )
            .all()
        )
        if not vt_rows:
            vt_rows = (
                db.query(TuDienVatTu)
                .filter(
                    TuDienVatTu.msvt.in_(vt_codes),
                    TuDienVatTu.regulation_code == regulation_code,
                    TuDienVatTu.source == "norm",
                )
                .all()
            )
        vt_map = {v.msvt: v for v in vt_rows}

    dinh_muc_list = []
    for dm in dm_rows:
        vt = vt_map.get(dm.msvt)
        rtype = ""
        if dm.msvt:
            if dm.msvt.startswith("V"):
                rtype = "VL"
            elif dm.msvt.startswith("N"):
                rtype = "NC"
            elif dm.msvt.startswith("M"):
                rtype = "MTC"
        dinh_muc_list.append(
            DinhMucResponse(
                mhdm=dm.mhdm,
                msvt=dm.msvt,
                tvt=vt.tvt if vt else None,
                dvt=vt.dvt if vt else None,
                hao_phi=dm.hao_phi,
                gia=vt.gia_goc if vt else 0,
                resource_type=rtype,
            )
        )

    plv_resp = None
    if item.plv:
        plv = (
            db.query(PhuLucVua)
            .filter(
                PhuLucVua.btm == item.plv,
                PhuLucVua.regulation_code == regulation_code,
            )
            .first()
        )
        if plv:
            plv_resp = PhuLucVuaResponse.model_validate(plv)

    return DonGiaDetailResponse(
        don_gia=DonGiaResponse.model_validate(item),
        dinh_muc=dinh_muc_list,
        phu_luc_vua=plv_resp,
    )


@router.get("/{mhdg}/compare")
def compare_don_gia(
    mhdg: str,
    sources: str = Query("norm"),
    regulation_code: str = Query("TT12-2021"),
    db_type: str = Query("XD+LD+SC"),
    db: Session = Depends(get_db),
):
    """Compare unit prices for a work item across multiple sources."""
    source_list = [s.strip() for s in sources.split(",") if s.strip()]
    if not source_list:
        from fastapi import HTTPException
        raise HTTPException(400, "At least one source is required")

    # Get base info from the first available source
    tcv = None
    dvt = None
    comparisons = []
    for src in source_list:
        calc = calculate_unit_price(db, mhdg, regulation_code, db_type, src)
        if "error" in calc:
            comparisons.append({
                "source": src,
                "vlc": None,
                "nc": None,
                "mtc": None,
                "total": None,
                "error": calc["error"],
            })
            continue
        if tcv is None:
            tcv = calc.get("tcv")
            dvt = calc.get("dvt")
        comparisons.append({
            "source": src,
            "vlc": calc["vlc"],
            "nc": calc["nc"],
            "mtc": calc["mtc"],
            "total": calc["vlc"] + calc["nc"] + calc["mtc"],
        })

    return {
        "mhdg": mhdg,
        "tcv": tcv,
        "dvt": dvt,
        "comparisons": comparisons,
    }


@router.get("/{mhdg}/phan-tich")
def phan_tich_don_gia(
    mhdg: str,
    regulation_code: str = Query("TT12-2021"),
    db_type: str = Query("XD+LD+SC"),
    source: str = Query("norm"),
    db: Session = Depends(get_db),
):
    return calculate_unit_price(db, mhdg, regulation_code, db_type, source)
