"""API endpoints cho suat von dau tu (SVDT)."""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.svdt import (
    SvdtCalculateRequest,
    SvdtCalculateResponse,
    SvdtCreate,
    SvdtImportResponse,
    SvdtResponse,
)
from app.services.svdt_service import (
    calculate_svdt,
    create_svdt,
    get_svdt,
    import_csv,
    search_svdt,
)

router = APIRouter(prefix="/svdt", tags=["svdt"])


@router.get("")
def list_svdt(
    q: str | None = Query(None, description="Tìm theo tên loại công trình"),
    nam: int | None = Query(None, description="Lọc theo năm"),
    quyet_dinh: str | None = Query(None, description="Lọc theo quyết định"),
    page: int = Query(1, ge=1, description="Trang"),
    limit: int = Query(20, ge=1, le=200, description="Số bản ghi mỗi trang"),
    db: Session = Depends(get_db),
):
    """Tìm kiếm và lọc suất vốn đầu tư."""
    result = search_svdt(db, q=q, nam=nam, quyet_dinh=quyet_dinh, page=page, limit=limit)
    # Chuyen items sang response model
    result["items"] = [SvdtResponse.model_validate(item) for item in result["items"]]
    return result


@router.get("/{svdt_id}", response_model=SvdtResponse)
def get_svdt_by_id(
    svdt_id: int,
    db: Session = Depends(get_db),
):
    """Lay suat von dau tu theo id."""
    record = get_svdt(db, svdt_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Khong tim thay suat von dau tu")
    return record


@router.post("", response_model=SvdtResponse)
def create_svdt_entry(
    data: SvdtCreate,
    db: Session = Depends(get_db),
):
    """Tao moi suat von dau tu."""
    return create_svdt(db, data)


@router.post("/calculate", response_model=SvdtCalculateResponse)
def calculate_svdt_estimate(
    req: SvdtCalculateRequest,
    db: Session = Depends(get_db),
):
    """Tinh uoc tinh chi phi tu suat von dau tu va dien tich."""
    result = calculate_svdt(db, req.svdt_id, req.dien_tich)
    if result is None:
        raise HTTPException(status_code=404, detail="Khong tim thay suat von dau tu")
    return result


@router.post("/import-csv", response_model=SvdtImportResponse)
async def import_svdt_csv(
    file: UploadFile,
    db: Session = Depends(get_db),
):
    """Import suat von dau tu tu file CSV."""
    content = await file.read()
    file_content = content.decode("utf-8-sig")
    return import_csv(db, file_content)
