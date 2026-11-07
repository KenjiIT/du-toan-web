"""Pydantic schemas cho he so gia nhan cong va gia ca may theo vung."""

from pydantic import BaseModel


class LaborPriceItem(BaseModel):
    """Mot dong gia nhan cong."""

    ma_nc: str
    nhom: str
    khu_vuc_i: float
    khu_vuc_ii: float

    model_config = {"from_attributes": True}


class LaborPriceResponse(BaseModel):
    """Danh sach gia nhan cong theo vung."""

    items: list[LaborPriceItem]
    total: int = 0
    page: int = 1
    limit: int = 20
    region: str
    decision_ref: str | None = None


class MachinePriceItem(BaseModel):
    """Mot dong gia ca may."""

    mh: str
    lm_tb: str
    gcm: float
    cpkh: float
    cpsc: float
    cpk: float
    cpnl: float
    cptl: float

    model_config = {"from_attributes": True}


class MachinePriceResponse(BaseModel):
    """Danh sach gia ca may theo vung va khu vuc."""

    items: list[MachinePriceItem]
    total: int = 0
    page: int = 1
    limit: int = 20
    region: str
    zone: str
    decision_ref: str | None = None


class RegionZoneInfo(BaseModel):
    """Thong tin vung va khu vuc co san."""

    region: str
    zones: list[str]
    decision_refs: list[str]
