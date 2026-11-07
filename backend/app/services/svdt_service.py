"""Service cho suat von dau tu (SVDT)."""

import csv
import io

from sqlalchemy.orm import Session

from app.models.svdt import SuatVonDauTu
from app.schemas.svdt import SvdtCreate


def search_svdt(
    db: Session,
    q: str | None = None,
    nam: int | None = None,
    quyet_dinh: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> dict:
    """Tim kiem va loc suat von dau tu voi phan trang."""
    query = db.query(SuatVonDauTu)

    if q:
        query = query.filter(SuatVonDauTu.loai_cong_trinh.ilike(f"%{q}%"))
    if nam is not None:
        query = query.filter(SuatVonDauTu.nam == nam)
    if quyet_dinh:
        query = query.filter(SuatVonDauTu.quyet_dinh.ilike(f"%{quyet_dinh}%"))

    total = query.count()
    offset = (page - 1) * limit
    items = query.order_by(SuatVonDauTu.id).offset(offset).limit(limit).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
    }


def get_svdt(db: Session, svdt_id: int) -> SuatVonDauTu | None:
    """Lay suat von dau tu theo id."""
    return db.query(SuatVonDauTu).filter(SuatVonDauTu.id == svdt_id).first()


def create_svdt(db: Session, data: SvdtCreate) -> SuatVonDauTu:
    """Tao moi suat von dau tu."""
    record = SuatVonDauTu(
        loai_cong_trinh=data.loai_cong_trinh,
        don_vi=data.don_vi,
        suat_von=data.suat_von,
        trong_do_xd=data.trong_do_xd or 0,
        trong_do_tb=data.trong_do_tb or 0,
        nam=data.nam,
        quyet_dinh=data.quyet_dinh,
        ghi_chu=data.ghi_chu,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def calculate_svdt(db: Session, svdt_id: int, dien_tich: float) -> dict | None:
    """Tinh uoc tinh tu suat von dau tu va dien tich."""
    record = get_svdt(db, svdt_id)
    if record is None:
        return None

    suat_von = record.suat_von or 0
    trong_do_xd = record.trong_do_xd or 0
    trong_do_tb = record.trong_do_tb or 0

    uoc_tinh_xd = trong_do_xd * dien_tich
    uoc_tinh_tb = trong_do_tb * dien_tich
    tong_uoc_tinh = suat_von * dien_tich

    return {
        "loai_cong_trinh": record.loai_cong_trinh,
        "don_vi": record.don_vi,
        "suat_von": suat_von,
        "dien_tich": dien_tich,
        "uoc_tinh_xd": uoc_tinh_xd,
        "uoc_tinh_tb": uoc_tinh_tb,
        "tong_uoc_tinh": tong_uoc_tinh,
    }


def import_csv(db: Session, file_content: str) -> dict:
    """Import suat von dau tu tu noi dung CSV.

    Cot CSV: loai_cong_trinh, don_vi, suat_von, trong_do_xd, trong_do_tb,
             nam, quyet_dinh, ghi_chu
    """
    reader = csv.DictReader(io.StringIO(file_content))
    created = 0
    errors: list[str] = []

    for i, row in enumerate(reader, start=2):  # dong 1 la header
        try:
            record = SuatVonDauTu(
                loai_cong_trinh=row.get("loai_cong_trinh", "").strip(),
                don_vi=row.get("don_vi", "").strip(),
                suat_von=_parse_float(row.get("suat_von")),
                trong_do_xd=_parse_float(row.get("trong_do_xd")),
                trong_do_tb=_parse_float(row.get("trong_do_tb")),
                nam=_parse_int(row.get("nam")),
                quyet_dinh=row.get("quyet_dinh", "").strip() or None,
                ghi_chu=row.get("ghi_chu", "").strip() or None,
            )
            db.add(record)
            created += 1
        except Exception as e:
            errors.append(f"Dong {i}: {e}")

    if created > 0:
        db.commit()

    return {"created": created, "errors": errors}


def _parse_float(value: str | None) -> float:
    """Chuyen chuoi thanh float, tra ve 0 neu khong hop le."""
    if not value or not value.strip():
        return 0
    try:
        return float(value.strip())
    except ValueError:
        return 0


def _parse_int(value: str | None) -> int | None:
    """Chuyen chuoi thanh int, tra ve None neu khong hop le."""
    if not value or not value.strip():
        return None
    try:
        return int(value.strip())
    except ValueError:
        return None
