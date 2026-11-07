"""API endpoints cho chi phi van chuyen (CVC)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.cvc import (
    CvcHsDiaHinh,
    CvcHsDoDoc,
    CvcHsLoaiDuong,
    CvcMaMay,
    CvcDmMay,
)
from app.schemas.cvc import (
    CvcCalculateRequest,
    CvcCalculateResponse,
    MaterialResponse,
    RoadTypeResponse,
    SlopeTypeResponse,
    TerrainTypeResponse,
    VehicleResponse,
)
from app.services.cvc_calculator import calculate_transport_cost

router = APIRouter(prefix="/cvc", tags=["cvc"])


@router.get("/vehicles", response_model=list[VehicleResponse])
def list_vehicles(db: Session = Depends(get_db)):
    """Danh sach phuong tien van chuyen."""
    rows = db.query(CvcMaMay).order_by(CvcMaMay.Id).all()
    return [
        VehicleResponse(id=r.Id, loaioto=r.loaioto or "", mamay=r.mamay or "")
        for r in rows
    ]


@router.get("/materials", response_model=list[MaterialResponse])
def list_materials(db: Session = Depends(get_db)):
    """Danh sach nhom vat lieu (distinct tu cvc_dm_may)."""
    rows = (
        db.query(CvcDmMay.vatlieu)
        .distinct()
        .order_by(CvcDmMay.vatlieu)
        .all()
    )
    return [MaterialResponse(vatlieu=r[0]) for r in rows if r[0]]


@router.get("/road-types", response_model=list[RoadTypeResponse])
def list_road_types(db: Session = Depends(get_db)):
    """Danh sach loai duong va he so."""
    rows = db.query(CvcHsLoaiDuong).order_by(CvcHsLoaiDuong.Id).all()
    return [
        RoadTypeResponse(id=r.Id, loaiduong=r.loaiduong or "", heso=r.heso or "")
        for r in rows
    ]


@router.get("/terrain-types", response_model=list[TerrainTypeResponse])
def list_terrain_types(db: Session = Depends(get_db)):
    """Danh sach dia hinh va he so."""
    rows = db.query(CvcHsDiaHinh).order_by(CvcHsDiaHinh.Id).all()
    return [
        TerrainTypeResponse(id=r.Id, diahinh=r.diahinh or "", heso=r.heso or "")
        for r in rows
    ]


@router.get("/slope-types", response_model=list[SlopeTypeResponse])
def list_slope_types(db: Session = Depends(get_db)):
    """Danh sach do doc va he so."""
    rows = db.query(CvcHsDoDoc).order_by(CvcHsDoDoc.Id).all()
    return [
        SlopeTypeResponse(id=r.Id, dodoc=r.dodoc or "", heso=r.heso or "")
        for r in rows
    ]


@router.post("/calculate", response_model=CvcCalculateResponse)
def calculate_cvc(
    req: CvcCalculateRequest,
    db: Session = Depends(get_db),
):
    """Tinh chi phi van chuyen cho vat lieu."""
    return calculate_transport_cost(db, req)
