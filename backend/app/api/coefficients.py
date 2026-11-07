"""API endpoints cho tra cuu he so gia nhan cong va gia ca may theo vung."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.coefficients import (
    LaborPriceResponse,
    MachinePriceResponse,
    RegionZoneInfo,
)
from app.services.coefficient_service import (
    get_available_regions,
    get_labor_prices,
    get_machine_prices,
)

router = APIRouter(prefix="/coefficients", tags=["coefficients"])


@router.get("/regions", response_model=list[RegionZoneInfo])
def list_regions(db: Session = Depends(get_db)):
    """Danh sach cac vung co du lieu gia nhan cong va gia ca may."""
    return get_available_regions(db)


@router.get("/labor-prices", response_model=LaborPriceResponse)
def list_labor_prices(
    region: str = Query(..., description="Tên vùng, vd: HoChiMinh, HaNoi"),
    q: str | None = Query(None, description="Tìm theo mã NC hoặc nhóm"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Giá nhân công theo vùng."""
    return get_labor_prices(db, region, q=q, page=page, limit=limit)


@router.get("/machine-prices", response_model=MachinePriceResponse)
def list_machine_prices(
    region: str = Query(..., description="Tên vùng, vd: HoChiMinh"),
    zone: str = Query(..., description="Khu vực: I hoặc II"),
    q: str | None = Query(None, description="Tìm theo mã hiệu hoặc tên máy"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Giá ca máy theo vùng và khu vực."""
    return get_machine_prices(db, region, zone, q=q, page=page, limit=limit)
