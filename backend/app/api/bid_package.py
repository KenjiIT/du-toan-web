# -*- coding: utf-8 -*-
"""API endpoints for bid package (goi thau) management."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.project import (
    BidPackageCreate,
    BidPackageDetail,
    BidPackageResponse,
    BidPackageSummary,
    BidPackageUpdate,
)
from app.services import bid_package_service

router = APIRouter(prefix="/projects", tags=["bid-packages"])


class ItemIdsBody(BaseModel):
    item_ids: list[int]


@router.get("/{project_id}/bid-packages", response_model=list[BidPackageSummary])
def list_bid_packages(project_id: int, db: Session = Depends(get_db)):
    """List all bid packages for a project with summaries."""
    return bid_package_service.get_bid_packages(db, project_id)


@router.post("/{project_id}/bid-packages", response_model=BidPackageResponse, status_code=201)
def create_bid_package(project_id: int, data: BidPackageCreate, db: Session = Depends(get_db)):
    """Create a new bid package."""
    return bid_package_service.create_bid_package(db, project_id, data)


@router.get("/{project_id}/bid-packages/{pkg_id}", response_model=BidPackageDetail)
def get_bid_package(project_id: int, pkg_id: int, db: Session = Depends(get_db)):
    """Get bid package detail with items and cost breakdown."""
    detail = bid_package_service.get_bid_package_detail(db, pkg_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Bid package not found")
    return detail


@router.put("/{project_id}/bid-packages/{pkg_id}", response_model=BidPackageResponse)
def update_bid_package(project_id: int, pkg_id: int, data: BidPackageUpdate, db: Session = Depends(get_db)):
    """Update a bid package."""
    pkg = bid_package_service.update_bid_package(db, pkg_id, data)
    if not pkg:
        raise HTTPException(status_code=404, detail="Bid package not found")
    return pkg


@router.delete("/{project_id}/bid-packages/{pkg_id}", status_code=204)
def delete_bid_package(project_id: int, pkg_id: int, db: Session = Depends(get_db)):
    """Delete a bid package."""
    if not bid_package_service.delete_bid_package(db, pkg_id):
        raise HTTPException(status_code=404, detail="Bid package not found")


@router.post("/{project_id}/bid-packages/{pkg_id}/assign-items")
def assign_items(project_id: int, pkg_id: int, body: ItemIdsBody, db: Session = Depends(get_db)):
    """Assign items to a bid package."""
    count = bid_package_service.assign_items(db, pkg_id, body.item_ids)
    return {"updated": count}


@router.post("/{project_id}/bid-packages/{pkg_id}/remove-items")
def remove_items(project_id: int, pkg_id: int, body: ItemIdsBody, db: Session = Depends(get_db)):
    """Remove items from a bid package."""
    count = bid_package_service.remove_items(db, pkg_id, body.item_ids)
    return {"updated": count}


@router.get("/{project_id}/bid-packages/{pkg_id}/export/excel")
def export_bid_package_excel(project_id: int, pkg_id: int, db: Session = Depends(get_db)):
    """Export bid package as Excel file."""
    buf = bid_package_service.generate_bid_package_excel(db, pkg_id)
    if not buf:
        raise HTTPException(status_code=404, detail="Bid package not found")

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=goi-thau-{pkg_id}.xlsx"},
    )
