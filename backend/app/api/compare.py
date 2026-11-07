# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends
from sqlalchemy import distinct
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.don_gia import DonGia, TuDienVatTu

router = APIRouter(prefix="/compare", tags=["compare"])


@router.get("/sources")
def get_compare_sources(db: Session = Depends(get_db)):
    """Return all available sources from don_gia and tu_dien_vat_tu tables."""
    dg_sources = db.query(distinct(DonGia.source)).filter(DonGia.source.isnot(None)).all()
    vt_sources = db.query(distinct(TuDienVatTu.source)).filter(TuDienVatTu.source.isnot(None)).all()

    all_sources = sorted({row[0] for row in dg_sources} | {row[0] for row in vt_sources})
    return all_sources
