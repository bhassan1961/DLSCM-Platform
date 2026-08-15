from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.marketplace import SurgeCapacityListing

router = APIRouter(prefix="/api/v1/marketplace", tags=["marketplace"])


# ── Schemas ────────────────────────────────────────────────────────────

class SurgeListingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    listing_type: str
    title: str
    description: Optional[str] = None
    capacity_value: float
    capacity_unit: str
    location: str
    latitude: float
    longitude: float
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    status: str
    created_at: Optional[datetime] = None


# ── Endpoints ──────────────────────────────────────────────────────────

@router.get("/", response_model=list[SurgeListingOut])
def list_surge_capacity(db: Session = Depends(get_db)):
    listings = db.query(SurgeCapacityListing).all()
    return [SurgeListingOut.model_validate(l) for l in listings]
