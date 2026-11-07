"""Pydantic schemas cho suat von dau tu (SVDT)."""

from pydantic import BaseModel


class SvdtResponse(BaseModel):
    """Thong tin suat von dau tu."""

    id: int
    loai_cong_trinh: str | None = None
    don_vi: str | None = None
    suat_von: float = 0
    trong_do_xd: float = 0
    trong_do_tb: float = 0
    nam: int | None = None
    quyet_dinh: str | None = None
    ghi_chu: str | None = None

    model_config = {"from_attributes": True}


class SvdtCreate(BaseModel):
    """Du lieu tao moi suat von dau tu."""

    loai_cong_trinh: str
    don_vi: str
    suat_von: float
    trong_do_xd: float = 0
    trong_do_tb: float = 0
    nam: int | None = None
    quyet_dinh: str | None = None
    ghi_chu: str | None = None


class SvdtCalculateRequest(BaseModel):
    """Yeu cau tinh uoc tinh tu suat von dau tu."""

    svdt_id: int
    dien_tich: float


class SvdtCalculateResponse(BaseModel):
    """Ket qua uoc tinh tu suat von dau tu."""

    loai_cong_trinh: str | None = None
    don_vi: str | None = None
    suat_von: float = 0
    dien_tich: float = 0
    uoc_tinh_xd: float = 0  # uoc tinh chi phi xay dung
    uoc_tinh_tb: float = 0  # uoc tinh chi phi thiet bi
    tong_uoc_tinh: float = 0  # tong uoc tinh


class SvdtImportResponse(BaseModel):
    """Ket qua import CSV suat von dau tu."""

    created: int
    errors: list[str]
