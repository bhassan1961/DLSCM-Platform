from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.disaster import Disaster

router = APIRouter(prefix="/api/v1/disasters", tags=["disasters"])


# ── Schemas ────────────────────────────────────────────────────────────


class DisasterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    disaster_type: str
    severity: str
    status: str
    country: str
    region: str | None = None
    latitude: float
    longitude: float
    affected_population: int
    start_date: datetime | None = None
    end_date: datetime | None = None
    description: str | None = None
    created_at: datetime | None = None


# ── Endpoints ──────────────────────────────────────────────────────────


@router.get("", response_model=list[DisasterOut])
def list_disasters(db: Session = Depends(get_db)):
    disasters = db.query(Disaster).all()
    return [DisasterOut.model_validate(d) for d in disasters]


@router.get("/{disaster_id}", response_model=DisasterOut)
def get_disaster(disaster_id: int, db: Session = Depends(get_db)):
    disaster = db.query(Disaster).filter(Disaster.id == disaster_id).first()
    if not disaster:
        raise HTTPException(status_code=404, detail="Disaster not found")
    return DisasterOut.model_validate(disaster)
