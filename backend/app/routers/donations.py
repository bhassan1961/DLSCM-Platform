from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.donation import DonationInKind

router = APIRouter(prefix="/api/v1/donations", tags=["donations"])


# ── Schemas ────────────────────────────────────────────────────────────

class DonationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    donor_name: str
    donor_contact: Optional[str] = None
    items_description: str
    category: str
    quantity: int
    unit: str
    quality_status: str
    warehouse_id: Optional[int] = None
    received_date: Optional[datetime] = None
    assessed_by: Optional[str] = None
    notes: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None


class DonationCreate(BaseModel):
    donor_name: str
    donor_contact: Optional[str] = None
    items_description: str
    category: str
    quantity: int
    unit: str
    quality_status: str = "pending_assessment"
    warehouse_id: Optional[int] = None
    received_date: Optional[datetime] = None
    assessed_by: Optional[str] = None
    notes: Optional[str] = None
    status: str = "received"


class DonationStatusUpdate(BaseModel):
    status: str


VALID_STATUSES = {"received", "assessed", "stored", "distributed", "rejected"}
VALID_QUALITY = {"pending_assessment", "acceptable", "requires_sorting", "rejected"}
VALID_CATEGORIES = {"food", "medical", "shelter", "nfi", "mixed", "clothing", "water", "other"}


# ── Endpoints ──────────────────────────────────────────────────────────

@router.get("", response_model=list[DonationOut])
def list_donations(
    status: Optional[str] = Query(None, description="Filter by donation status"),
    db: Session = Depends(get_db),
):
    query = db.query(DonationInKind)
    if status:
        query = query.filter(DonationInKind.status == status)
    donations = query.all()
    return [DonationOut.model_validate(d) for d in donations]


@router.post("", response_model=DonationOut)
def create_donation(donation: DonationCreate, db: Session = Depends(get_db)):
    if donation.category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of: {VALID_CATEGORIES}")
    if donation.quality_status not in VALID_QUALITY:
        raise HTTPException(status_code=400, detail=f"Invalid quality_status. Must be one of: {VALID_QUALITY}")
    if donation.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {VALID_STATUSES}")
    d = DonationInKind(**donation.model_dump())
    db.add(d)
    db.commit()
    db.refresh(d)
    return DonationOut.model_validate(d)


@router.patch("/{donation_id}/status", response_model=DonationOut)
def update_donation_status(donation_id: int, update: DonationStatusUpdate, db: Session = Depends(get_db)):
    if update.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {VALID_STATUSES}")
    d = db.query(DonationInKind).filter(DonationInKind.id == donation_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Donation not found")
    d.status = update.status
    db.commit()
    db.refresh(d)
    return DonationOut.model_validate(d)
