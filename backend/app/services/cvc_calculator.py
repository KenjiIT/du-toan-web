"""Service tinh chi phi van chuyen (CVC).

Logic:
- Van chuyen co gioi: tra bang cvc_dm_may theo vat lieu, phuong tien, cu ly
  rồi nhan cac he so (loai duong, dia hinh, do doc).
- Van chuyen thu cong: tra bang cvc_dm_thucong (10m khoi diem + 10m tiep theo)
  rồi nhan cac he so dia hinh, do doc (loai duong khong ap dung cho thu cong).
"""

from sqlalchemy.orm import Session

from app.models.cvc import (
    CvcDmMay,
    CvcDmThuCong,
    CvcHsDiaHinh,
    CvcHsDoDoc,
    CvcHsLoaiDuong,
    CvcMaMay,
)
from app.schemas.cvc import (
    CvcCalculateRequest,
    CvcCalculateResponse,
    MachineTransportDetail,
    ManualTransportDetail,
)


# Thu tu uu tien cu ly: nho -> lon
_CULY_ORDER = ["≤1km", "≤10km", "≤60km", ">60km"]


def _pick_culy(distance_km: float) -> str:
    """Chon muc cu ly phu hop voi khoang cach."""
    if distance_km <= 1:
        return "≤1km"
    if distance_km <= 10:
        return "≤10km"
    if distance_km <= 60:
        return "≤60km"
    return ">60km"


def _calc_manual(
    db: Session,
    vatlieu: str,
    culy_m: float,
    terrain_coeff: float,
    slope_coeff: float,
) -> ManualTransportDetail | None:
    """Tinh van chuyen thu cong.

    Cu ly thuc cong tinh theo met.
    haophi = haophi_khoi_diem (10m dau) + haophi_tiep_theo * ((cu_ly - 10) / 10)
    """
    # Tim nhom vat lieu gan dung nhat (ten trong cvc_dm_thucong khac voi cvc_dm_may)
    base_row = (
        db.query(CvcDmThuCong)
        .filter(
            CvcDmThuCong.nhomvatlieu.contains(vatlieu),
            CvcDmThuCong.culy.contains("khởi điểm") | CvcDmThuCong.culy.contains("khời điểm"),
        )
        .first()
    )
    if not base_row:
        return None

    nhom = base_row.nhomvatlieu
    haophi_base = base_row.haophi_f
    boclen = base_row.boclen_f
    bocxuong = base_row.bocxuong_f
    donvi = base_row.donvi or ""

    # Tim dong "10m tiep theo"
    extra_row = (
        db.query(CvcDmThuCong)
        .filter(
            CvcDmThuCong.nhomvatlieu == nhom,
            CvcDmThuCong.culy.contains("tiếp theo"),
        )
        .first()
    )

    haophi_extra = 0.0
    if extra_row and culy_m > 10:
        steps = (culy_m - 10) / 10
        haophi_extra = extra_row.haophi_f * steps

    haophi_total = haophi_base + haophi_extra
    adjusted = haophi_total * terrain_coeff * slope_coeff

    return ManualTransportDetail(
        nhomvatlieu=nhom,
        culy_m=culy_m,
        haophi_base=round(haophi_base, 6),
        haophi_extra=round(haophi_extra, 6),
        haophi_total=round(haophi_total, 6),
        donvi=donvi,
        boclen=round(boclen, 6),
        bocxuong=round(bocxuong, 6),
        terrain_coeff=terrain_coeff,
        slope_coeff=slope_coeff,
        adjusted_haophi=round(adjusted, 6),
    )


def calculate_transport_cost(
    db: Session,
    req: CvcCalculateRequest,
) -> CvcCalculateResponse:
    """Tinh chi phi van chuyen co gioi va thu cong."""

    # --- Tra cac he so ---
    road = db.query(CvcHsLoaiDuong).filter(CvcHsLoaiDuong.Id == req.loaiduong_id).first()
    terrain = db.query(CvcHsDiaHinh).filter(CvcHsDiaHinh.Id == req.diahinh_id).first()
    slope = db.query(CvcHsDoDoc).filter(CvcHsDoDoc.Id == req.dodoc_id).first()

    road_coeff = road.heso_f if road else 1.0
    terrain_coeff = terrain.heso_f if terrain else 1.0
    slope_coeff = slope.heso_f if slope else 1.0

    loaiduong_label = road.loaiduong if road else ""
    diahinh_label = terrain.diahinh if terrain else ""
    dodoc_label = slope.dodoc if slope else ""

    # --- Van chuyen co gioi ---
    machine_detail: MachineTransportDetail | None = None

    # Xac dinh phuong tien
    vehicle_code: str | None = None
    vehicle_name: str | None = None
    if req.vehicle_id:
        v = db.query(CvcMaMay).filter(CvcMaMay.Id == req.vehicle_id).first()
        if v:
            vehicle_code = v.mamay
            vehicle_name = v.loaioto

    culy_key = _pick_culy(req.culy_km)

    # Tra bang dinh muc may
    q = db.query(CvcDmMay).filter(
        CvcDmMay.vatlieu == req.vatlieu,
        CvcDmMay.culy == culy_key,
    )
    if vehicle_code:
        q = q.filter(CvcDmMay.phuongtien == vehicle_code)

    dm_may = q.first()
    if dm_may:
        haophi = dm_may.haophi_f
        adjusted = haophi * road_coeff * terrain_coeff * slope_coeff

        # Neu chua co ten xe, tra tu cvc_ma_may
        if not vehicle_name:
            v = db.query(CvcMaMay).filter(CvcMaMay.mamay == dm_may.phuongtien).first()
            vehicle_name = v.loaioto if v else None

        machine_detail = MachineTransportDetail(
            vatlieu=dm_may.vatlieu or "",
            phuongtien=dm_may.phuongtien or "",
            loaioto=vehicle_name,
            culy=dm_may.culy or "",
            haophi=round(haophi, 6),
            donvi=dm_may.donvi or "",
            quydoidv=dm_may.quydoidv_f,
            road_coeff=road_coeff,
            terrain_coeff=terrain_coeff,
            slope_coeff=slope_coeff,
            adjusted_haophi=round(adjusted, 6),
        )

    # --- Van chuyen thu cong ---
    # Chuyen km -> m cho thu cong
    culy_m = req.culy_km * 1000
    manual_detail = _calc_manual(db, req.vatlieu, culy_m, terrain_coeff, slope_coeff)

    return CvcCalculateResponse(
        machine=machine_detail,
        manual=manual_detail,
        loaiduong=loaiduong_label,
        diahinh=diahinh_label,
        dodoc=dodoc_label,
    )
