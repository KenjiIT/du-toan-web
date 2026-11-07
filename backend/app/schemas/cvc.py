"""Pydantic schemas cho CVC (chi phi van chuyen)."""

from pydantic import BaseModel


# --- Response schemas cho lookup endpoints ---


class VehicleResponse(BaseModel):
    """Phuong tien van chuyen."""

    id: str
    loaioto: str
    mamay: str

    model_config = {"from_attributes": True}


class MaterialResponse(BaseModel):
    """Nhom vat lieu."""

    vatlieu: str


class RoadTypeResponse(BaseModel):
    """Loai duong va he so."""

    id: str
    loaiduong: str
    heso: str

    model_config = {"from_attributes": True}


class TerrainTypeResponse(BaseModel):
    """Dia hinh va he so."""

    id: str
    diahinh: str
    heso: str

    model_config = {"from_attributes": True}


class SlopeTypeResponse(BaseModel):
    """Do doc va he so."""

    id: str
    dodoc: str
    heso: str

    model_config = {"from_attributes": True}


# --- Request / response cho calculator ---


class CvcCalculateRequest(BaseModel):
    """Yeu cau tinh chi phi van chuyen."""

    vatlieu: str  # ten nhom vat lieu, vd "Cat"
    culy_km: float  # cu ly van chuyen (km)
    vehicle_id: str | None = None  # Id trong cvc_ma_may (None = tu dong chon)
    loaiduong_id: str = "3"  # Id trong cvc_hs_loaiduong, mac dinh loai 3 (he so 1)
    diahinh_id: str = "1"  # Id trong cvc_hs_diahinh, mac dinh binh thuong
    dodoc_id: str = "1"  # Id trong cvc_hs_dodoc, mac dinh <= 7 do


class MachineTransportDetail(BaseModel):
    """Chi tiet tinh van chuyen co gioi."""

    vatlieu: str
    phuongtien: str
    loaioto: str | None = None
    culy: str
    haophi: float
    donvi: str
    quydoidv: float
    road_coeff: float
    terrain_coeff: float
    slope_coeff: float
    adjusted_haophi: float  # haophi * cac he so


class ManualTransportDetail(BaseModel):
    """Chi tiet tinh van chuyen thu cong."""

    nhomvatlieu: str
    culy_m: float
    haophi_base: float  # 10m khoi diem
    haophi_extra: float  # 10m tiep theo * so buoc
    haophi_total: float
    donvi: str
    boclen: float
    bocxuong: float
    terrain_coeff: float
    slope_coeff: float
    adjusted_haophi: float  # tong * cac he so


class CvcCalculateResponse(BaseModel):
    """Ket qua tinh chi phi van chuyen."""

    machine: MachineTransportDetail | None = None
    manual: ManualTransportDetail | None = None
    loaiduong: str
    diahinh: str
    dodoc: str
