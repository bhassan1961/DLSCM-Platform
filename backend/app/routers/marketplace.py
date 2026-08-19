from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, timezone
import math

from app.database import get_db
from app.models.marketplace import SurgeCapacityListing
from app.models.booking import MarketplaceBooking

router = APIRouter(prefix="/api/v1/marketplace", tags=["marketplace"])


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


class BookingCreate(BaseModel):
    requester_org: str
    quantity_needed: float
    notes: Optional[str] = None


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    listing_id: int
    requester_org: str
    quantity_needed: float
    notes: Optional[str] = None
    status: str
    booked_at: Optional[datetime] = None


@router.get("", response_model=list[SurgeListingOut])
def list_surge_capacity(db: Session = Depends(get_db)):
    listings = db.query(SurgeCapacityListing).all()
    return [SurgeListingOut.model_validate(l) for l in listings]


@router.post("/{listing_id}/match")
def match_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(SurgeCapacityListing).filter(SurgeCapacityListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    all_listings = db.query(SurgeCapacityListing).filter(
        SurgeCapacityListing.id != listing_id,
        SurgeCapacityListing.status == "available",
    ).all()

    def _score(other):
        type_match = 1.0 if other.listing_type == listing.listing_type else 0.3
        dlat = abs(other.latitude - listing.latitude)
        dlng = abs(other.longitude - listing.longitude)
        dist = math.sqrt(dlat**2 + dlng**2)
        proximity = max(0, 1 - dist / 50)
        capacity_ratio = min(other.capacity_value, listing.capacity_value) / max(other.capacity_value, listing.capacity_value, 1)
        return round(type_match * 0.3 + proximity * 0.4 + capacity_ratio * 0.3, 3)

    scored = [(l, _score(l)) for l in all_listings]
    scored.sort(key=lambda x: x[1], reverse=True)

    return {
        "listing_id": listing_id,
        "matches": [
            {
                "id": l.id,
                "title": l.title,
                "listing_type": l.listing_type,
                "location": l.location,
                "capacity_value": l.capacity_value,
                "capacity_unit": l.capacity_unit,
                "score": s,
            }
            for l, s in scored[:5]
        ],
    }


@router.post("/{listing_id}/book")
def book_listing(listing_id: int, req: BookingCreate, db: Session = Depends(get_db)):
    listing = db.query(SurgeCapacityListing).filter(SurgeCapacityListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.status != "available":
        raise HTTPException(status_code=400, detail="Listing is not available for booking")

    listing.status = "reserved"

    booking = MarketplaceBooking(
        listing_id=listing_id,
        requester_org=req.requester_org,
        quantity_needed=req.quantity_needed,
        notes=req.notes,
        status="confirmed",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    return {
        "id": booking.id,
        "listing_id": listing_id,
        "listing_title": listing.title,
        "listing_type": listing.listing_type,
        "location": listing.location,
        "requester_org": booking.requester_org,
        "quantity_needed": booking.quantity_needed,
        "notes": booking.notes,
        "status": booking.status,
        "booked_at": booking.booked_at.isoformat() if booking.booked_at else None,
    }


@router.get("/bookings")
def list_bookings(db: Session = Depends(get_db)):
    bookings = db.query(MarketplaceBooking).all()
    results = []
    for b in bookings:
        listing = db.query(SurgeCapacityListing).filter(SurgeCapacityListing.id == b.listing_id).first()
        results.append({
            "id": b.id,
            "listing_id": b.listing_id,
            "listing_title": listing.title if listing else None,
            "listing_type": listing.listing_type if listing else None,
            "location": listing.location if listing else None,
            "requester_org": b.requester_org,
            "quantity_needed": b.quantity_needed,
            "notes": b.notes,
            "status": b.status,
            "booked_at": b.booked_at.isoformat() if b.booked_at else None,
        })
    return results


@router.patch("/bookings/{booking_id}/cancel")
def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(MarketplaceBooking).filter(MarketplaceBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking.status = "cancelled"

    listing = db.query(SurgeCapacityListing).filter(SurgeCapacityListing.id == booking.listing_id).first()
    if listing:
        listing.status = "available"

    db.commit()

    return {
        "id": booking.id,
        "listing_id": booking.listing_id,
        "listing_title": listing.title if listing else None,
        "listing_type": listing.listing_type if listing else None,
        "location": listing.location if listing else None,
        "requester_org": booking.requester_org,
        "quantity_needed": booking.quantity_needed,
        "notes": booking.notes,
        "status": booking.status,
        "booked_at": booking.booked_at.isoformat() if booking.booked_at else None,
    }
