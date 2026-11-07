from pydantic import BaseModel


class DonGiaResponse(BaseModel):
    mhdg: str
    tcv: str | None = None
    dvt: str | None = None
    vlc: float | None = 0
    vlp: float | None = 0
    nc: float | None = 0
    mtc: float | None = 0
    plv: str | None = None
    regulation_code: str = ""
    source: str | None = None

    model_config = {"from_attributes": True}


class DonGiaSearchResponse(BaseModel):
    items: list[DonGiaResponse]
    total: int
    page: int
    limit: int


class DinhMucResponse(BaseModel):
    mhdm: str
    msvt: str
    tvt: str | None = None
    dvt: str | None = None
    hao_phi: float | None = 0
    gia: float | None = 0
    resource_type: str = ""

    model_config = {"from_attributes": True}


class PhuLucVuaResponse(BaseModel):
    btm: str
    tg: str | None = None
    dvt: str | None = None
    mxm: str | None = None
    hpxm: float | None = 0
    cat: str | None = None
    hpc: float | None = 0
    da: str | None = None
    hpd: float | None = 0
    vcuc: str | None = None
    hpv: float | None = 0

    model_config = {"from_attributes": True}


class DonGiaDetailResponse(BaseModel):
    don_gia: DonGiaResponse
    dinh_muc: list[DinhMucResponse]
    phu_luc_vua: PhuLucVuaResponse | None = None


class ChapterResponse(BaseModel):
    code: str
    name: str
    count: int
