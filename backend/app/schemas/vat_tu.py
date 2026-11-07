from pydantic import BaseModel


class VatTuResponse(BaseModel):
    id: int
    msvt: str
    tvt: str | None = None
    dvt: str | None = None
    gia_goc: float | None = 0
    lvt: str | None = None
    regulation_code: str = ""
    source: str | None = None

    model_config = {"from_attributes": True}


class VatTuSearchResponse(BaseModel):
    items: list[VatTuResponse]
    total: int
    page: int
    limit: int


class VatTuPriceUpdate(BaseModel):
    gia_goc: float


class VatTuImportResult(BaseModel):
    created: int
    updated: int
