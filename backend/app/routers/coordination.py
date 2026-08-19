from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.coordination import ThreeWEntry

router = APIRouter(prefix="/api/v1/coordination", tags=["coordination"])


# ── Schemas ────────────────────────────────────────────────────────────


class ThreeWOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    organization_name: str | None = None
    disaster_id: int
    activity: str
    location: str
    latitude: float
    longitude: float
    beneficiaries: int
    start_date: datetime | None = None
    end_date: datetime | None = None
    status: str
    notes: str | None = None
    created_at: datetime | None = None


class ThreeWCreate(BaseModel):
    organization_id: int
    disaster_id: int
    activity: str
    location: str
    latitude: float
    longitude: float
    beneficiaries: int
    start_date: datetime | None = None
    end_date: datetime | None = None
    status: str = "active"
    notes: str | None = None


class ThreeWUpdate(BaseModel):
    activity: str | None = None
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    beneficiaries: int | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    status: str | None = None
    notes: str | None = None


# ── Endpoints ──────────────────────────────────────────────────────────


@router.get("", response_model=list[ThreeWOut])
def list_threew(db: Session = Depends(get_db)):
    entries = db.query(ThreeWEntry).options(joinedload(ThreeWEntry.organization)).all()
    results = []
    for entry in entries:
        data = ThreeWOut.model_validate(entry)
        data.organization_name = entry.organization.name if entry.organization else None
        results.append(data)
    return results


@router.post("", response_model=ThreeWOut, status_code=201)
def create_threew(entry: ThreeWCreate, db: Session = Depends(get_db)):
    e = ThreeWEntry(**entry.model_dump())
    db.add(e)
    db.commit()
    db.refresh(e)
    data = ThreeWOut.model_validate(e)
    data.organization_name = e.organization.name if e.organization else None
    return data


@router.patch("/{entry_id}", response_model=ThreeWOut)
def update_threew(entry_id: int, update: ThreeWUpdate, db: Session = Depends(get_db)):
    e = (
        db.query(ThreeWEntry)
        .options(joinedload(ThreeWEntry.organization))
        .filter(ThreeWEntry.id == entry_id)
        .first()
    )
    if not e:
        raise HTTPException(status_code=404, detail="3W entry not found")
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(e, field, value)
    db.commit()
    db.refresh(e)
    data = ThreeWOut.model_validate(e)
    data.organization_name = e.organization.name if e.organization else None
    return data


@router.delete("/{entry_id}", status_code=204)
def delete_threew(entry_id: int, db: Session = Depends(get_db)):
    e = db.query(ThreeWEntry).filter(ThreeWEntry.id == entry_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="3W entry not found")
    db.delete(e)
    db.commit()
