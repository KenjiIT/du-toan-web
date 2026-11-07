import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.don_gia import TuDienVatTu
from app.schemas.vat_tu import (
    VatTuImportResult,
    VatTuPriceUpdate,
    VatTuResponse,
    VatTuSearchResponse,
)

router = APIRouter(prefix="/vat-tu", tags=["vat-tu"])


@router.get("", response_model=VatTuSearchResponse)
def search_vat_tu(
    q: str | None = None,
    regulation_code: str = Query("TT12-2021"),
    source: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(TuDienVatTu).filter(
        TuDienVatTu.regulation_code == regulation_code,
    )

    if source:
        query = query.filter(TuDienVatTu.source == source)
    else:
        query = query.filter(TuDienVatTu.source == "norm")

    if q:
        query = query.filter(
            TuDienVatTu.msvt.contains(q) | TuDienVatTu.tvt.contains(q)
        )

    total = query.count()
    items = query.order_by(TuDienVatTu.msvt).offset((page - 1) * limit).limit(limit).all()

    return VatTuSearchResponse(
        items=[VatTuResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{msvt}", response_model=VatTuResponse)
def get_vat_tu(
    msvt: str,
    regulation_code: str = Query("TT12-2021"),
    source: str = Query("norm"),
    db: Session = Depends(get_db),
):
    item = (
        db.query(TuDienVatTu)
        .filter(
            TuDienVatTu.msvt == msvt,
            TuDienVatTu.regulation_code == regulation_code,
            TuDienVatTu.source == source,
        )
        .first()
    )
    if not item:
        raise HTTPException(404, f"Material {msvt} not found")
    return VatTuResponse.model_validate(item)


@router.get("/{msvt}/compare")
def compare_vat_tu(
    msvt: str,
    sources: str = Query("norm"),
    regulation_code: str = Query("TT12-2021"),
    db: Session = Depends(get_db),
):
    """Compare material prices across multiple sources."""
    source_list = [s.strip() for s in sources.split(",") if s.strip()]
    if not source_list:
        raise HTTPException(400, "At least one source is required")

    tvt = None
    dvt = None
    comparisons = []
    for src in source_list:
        item = (
            db.query(TuDienVatTu)
            .filter(
                TuDienVatTu.msvt == msvt,
                TuDienVatTu.regulation_code == regulation_code,
                TuDienVatTu.source == src,
            )
            .first()
        )
        if not item:
            comparisons.append({
                "source": src,
                "gia_goc": None,
                "error": f"Material {msvt} not found for source {src}",
            })
            continue
        if tvt is None:
            tvt = item.tvt
            dvt = item.dvt
        comparisons.append({
            "source": src,
            "gia_goc": item.gia_goc,
        })

    return {
        "msvt": msvt,
        "tvt": tvt,
        "dvt": dvt,
        "comparisons": comparisons,
    }


@router.patch("/{id}", response_model=VatTuResponse)
def update_vat_tu_price(
    id: int,
    body: VatTuPriceUpdate,
    db: Session = Depends(get_db),
):
    item = db.query(TuDienVatTu).filter(TuDienVatTu.id == id).first()
    if not item:
        raise HTTPException(404, f"Material id={id} not found")
    item.gia_goc = body.gia_goc
    db.commit()
    db.refresh(item)
    return VatTuResponse.model_validate(item)


@router.post("/import-csv", response_model=VatTuImportResult)
async def import_vat_tu_csv(
    file: UploadFile = File(...),
    regulation_code: str = Query("TT12-2021"),
    db: Session = Depends(get_db),
):
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    created = 0
    updated = 0

    for row in reader:
        msvt = row.get("msvt", "").strip()
        if not msvt:
            continue

        source = row.get("source", "").strip() or "import"

        existing = (
            db.query(TuDienVatTu)
            .filter(
                TuDienVatTu.msvt == msvt,
                TuDienVatTu.regulation_code == regulation_code,
            )
            .first()
        )

        gia_goc_str = row.get("gia_goc", "0").strip()
        try:
            gia_goc = float(gia_goc_str) if gia_goc_str else 0
        except ValueError:
            gia_goc = 0

        if existing:
            existing.gia_goc = gia_goc
            if source != "import":
                existing.source = source
            updated += 1
        else:
            new_item = TuDienVatTu(
                msvt=msvt,
                tvt=row.get("tvt", "").strip() or None,
                dvt=row.get("dvt", "").strip() or None,
                gia_goc=gia_goc,
                source=source,
                regulation_code=regulation_code,
                db_type="XD+LD+SC",
            )
            db.add(new_item)
            created += 1

    db.commit()
    return VatTuImportResult(created=created, updated=updated)
