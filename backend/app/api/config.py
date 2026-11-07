from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.config import Region, Regulation

router = APIRouter(prefix="/config", tags=["config"])


class RegulationResponse(BaseModel):
    id: int
    code: str
    name: str | None = None
    description: str | None = None

    model_config = {"from_attributes": True}


class RegionResponse(BaseModel):
    id: int
    name: str
    category: str | None = None

    model_config = {"from_attributes": True}


@router.get("/regulations", response_model=list[RegulationResponse])
def list_regulations(db: Session = Depends(get_db)):
    return db.query(Regulation).order_by(Regulation.sort_order).all()


@router.get("/regions", response_model=list[RegionResponse])
def list_regions(
    category: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Region)
    if category:
        query = query.filter(Region.category == category)
    return query.order_by(Region.name).all()
