from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from datetime import datetime

import uuid

from app.database import get_db
from app.models.shipment import Shipment, ShipmentLeg, ShipmentTrackingEvent
from app.models.inventory import Warehouse
from app.services.customs import generate_customs_docs

router = APIRouter(prefix="/api/v1/shipments", tags=["shipments"])


# ── Schemas ────────────────────────────────────────────────────────────

class ShipmentLegOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shipment_id: int
    leg_order: int
    from_lat: float
    from_lng: float
    to_lat: float
    to_lng: float
    mode: str
    distance_km: float
    duration_hours: float
    carrier: Optional[str] = None
    from_location: Optional[str] = None
    to_location: Optional[str] = None


class TrackingEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shipment_id: int
    event_type: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    metadata: Optional[Any] = None
    timestamp: Optional[datetime] = None


class ShipmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tracking_id: str
    request_id: int
    origin_warehouse_id: int
    status: str
    transport_mode: str
    carrier: Optional[str] = None
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    eta: Optional[datetime] = None
    departed_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    notes: Optional[str] = None
    customs_status: Optional[str] = None
    customs_docs: Optional[Any] = None
    created_at: Optional[datetime] = None
    legs: list[ShipmentLegOut] = []
    tracking_events: list[TrackingEventOut] = []


class ShipmentCreate(BaseModel):
    request_id: int
    origin_warehouse_id: int
    transport_mode: str
    carrier: Optional[str] = None
    eta: Optional[datetime] = None
    notes: Optional[str] = None


class MultiLegCreate(BaseModel):
    request_id: int
    origin_warehouse_id: int
    legs: list[dict]
    carrier: Optional[str] = None
    notes: Optional[str] = None


class ShipmentStatusUpdate(BaseModel):
    status: str


class TrackingEventCreate(BaseModel):
    event_type: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None


VALID_STATUSES = {"preparing", "in_transit", "delivered", "delayed", "customs_hold"}


def _load_shipment(db, shipment_id):
    return (
        db.query(Shipment)
        .options(joinedload(Shipment.legs), joinedload(Shipment.tracking_events))
        .filter(Shipment.id == shipment_id)
        .first()
    )


# ── Endpoints ──────────────────────────────────────────────────────────

@router.get("", response_model=list[ShipmentOut])
def list_shipments(db: Session = Depends(get_db)):
    shipments = (
        db.query(Shipment)
        .options(joinedload(Shipment.legs), joinedload(Shipment.tracking_events))
        .all()
    )
    return [ShipmentOut.model_validate(s) for s in shipments]


@router.post("", response_model=ShipmentOut, status_code=201)
def create_shipment(shipment: ShipmentCreate, db: Session = Depends(get_db)):
    tracking_id = f"SHP-{uuid.uuid4().hex[:8].upper()}"
    s = Shipment(
        tracking_id=tracking_id,
        request_id=shipment.request_id,
        origin_warehouse_id=shipment.origin_warehouse_id,
        transport_mode=shipment.transport_mode,
        carrier=shipment.carrier,
        eta=shipment.eta,
        notes=shipment.notes,
        status="preparing",
    )
    db.add(s)
    db.commit()
    db.refresh(s)

    event = ShipmentTrackingEvent(
        shipment_id=s.id,
        event_type="created",
        description=f"Shipment created with tracking ID {tracking_id}",
    )
    db.add(event)
    db.commit()

    return ShipmentOut.model_validate(_load_shipment(db, s.id))


@router.post("/multi-leg", response_model=ShipmentOut, status_code=201)
def create_multi_leg_shipment(req: MultiLegCreate, db: Session = Depends(get_db)):
    tracking_id = f"SHP-{uuid.uuid4().hex[:8].upper()}"
    primary_mode = req.legs[0]["mode"] if req.legs else "road"
    s = Shipment(
        tracking_id=tracking_id,
        request_id=req.request_id,
        origin_warehouse_id=req.origin_warehouse_id,
        transport_mode=primary_mode,
        carrier=req.carrier,
        notes=req.notes,
        status="preparing",
    )
    db.add(s)
    db.flush()

    for i, leg in enumerate(req.legs):
        db.add(ShipmentLeg(
            shipment_id=s.id,
            leg_order=i + 1,
            from_lat=leg["from_lat"],
            from_lng=leg["from_lng"],
            to_lat=leg["to_lat"],
            to_lng=leg["to_lng"],
            mode=leg.get("mode", primary_mode),
            distance_km=leg.get("distance_km", 0),
            duration_hours=leg.get("duration_hours", 0),
            carrier=leg.get("carrier"),
            from_location=leg.get("from_location"),
            to_location=leg.get("to_location"),
        ))

    event = ShipmentTrackingEvent(
        shipment_id=s.id,
        event_type="created",
        description=f"Multi-leg shipment created: {len(req.legs)} legs, modes: {', '.join(set(l.get('mode', primary_mode) for l in req.legs))}",
    )
    db.add(event)
    db.commit()

    return ShipmentOut.model_validate(_load_shipment(db, s.id))


@router.patch("/{shipment_id}/status", response_model=ShipmentOut)
def update_shipment_status(shipment_id: int, update: ShipmentStatusUpdate, db: Session = Depends(get_db)):
    if update.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {VALID_STATUSES}")
    s = _load_shipment(db, shipment_id)
    if not s:
        raise HTTPException(status_code=404, detail="Shipment not found")

    old_status = s.status
    s.status = update.status
    if update.status == "delivered":
        from datetime import datetime, timezone
        s.delivered_at = datetime.now(timezone.utc)
    elif update.status == "in_transit" and not s.departed_at:
        from datetime import datetime, timezone
        s.departed_at = datetime.now(timezone.utc)

    event = ShipmentTrackingEvent(
        shipment_id=s.id,
        event_type="status_change",
        description=f"Status changed: {old_status} → {update.status}",
        latitude=s.current_lat,
        longitude=s.current_lng,
    )
    db.add(event)
    db.commit()
    db.refresh(s)
    return ShipmentOut.model_validate(_load_shipment(db, s.id))


@router.post("/{shipment_id}/tracking", response_model=TrackingEventOut, status_code=201)
def add_tracking_event(shipment_id: int, event: TrackingEventCreate, db: Session = Depends(get_db)):
    s = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Shipment not found")

    te = ShipmentTrackingEvent(
        shipment_id=s.id,
        event_type=event.event_type,
        location=event.location,
        latitude=event.latitude,
        longitude=event.longitude,
        description=event.description,
    )
    db.add(te)

    if event.latitude is not None:
        s.current_lat = event.latitude
        s.current_lng = event.longitude

    db.commit()
    db.refresh(te)
    return TrackingEventOut.model_validate(te)


@router.post("/{shipment_id}/customs-docs")
def generate_shipment_customs_docs(shipment_id: int, db: Session = Depends(get_db)):
    s = (
        db.query(Shipment)
        .options(joinedload(Shipment.origin_warehouse))
        .filter(Shipment.id == shipment_id)
        .first()
    )
    if not s:
        raise HTTPException(status_code=404, detail="Shipment not found")

    warehouse = s.origin_warehouse
    if not warehouse:
        raise HTTPException(status_code=400, detail="Origin warehouse not found")

    org = db.query(Warehouse).filter(Warehouse.id == warehouse.id).first()

    docs = generate_customs_docs(
        shipment_tracking_id=s.tracking_id,
        origin_country=warehouse.location.split(",")[-1].strip() if warehouse.location else "Unknown",
        destination_country="Destination",
        items=[],
        organization_name="DLSCM Operations",
        transport_mode=s.transport_mode,
    )

    s.customs_docs = docs
    s.customs_status = "pending"

    event = ShipmentTrackingEvent(
        shipment_id=s.id,
        event_type="customs_docs_generated",
        description="Customs documentation generated",
    )
    db.add(event)
    db.commit()
    return docs


@router.delete("/{shipment_id}", status_code=204)
def delete_shipment(shipment_id: int, db: Session = Depends(get_db)):
    s = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Shipment not found")
    db.delete(s)
    db.commit()
    return None
