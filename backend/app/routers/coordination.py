from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.coordination import ThreeWEntry

router = APIRouter(prefix="/api/v1/coordination", tags=["coordination"])


# ── Schemas ────────────────────────────────────────────────────────────

class ThreeWOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    organization_name: Optional[str] = None
    disaster_id: int
    activity: str
    location: str
    latitude: float
    longitude: float
    beneficiaries: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


# ── Endpoints ──────────────────────────────────────────────────────────

@router.get("/", response_model=list[ThreeWOut])
def list_threew(db: Session = Depends(get_db)):
    entries = (
        db.query(ThreeWEntry)
        .options(joinedload(ThreeWEntry.organization))
        .all()
    )
    results = []
    for entry in entries:
        data = ThreeWOut.model_validate(entry)
        data.organization_name = entry.organization.name if entry.organization else None
        results.append(data)
    return results
