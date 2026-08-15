from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.shipment import Shipment, ShipmentLeg

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
    created_at: Optional[datetime] = None
    legs: list[ShipmentLegOut] = []


# ── Endpoints ──────────────────────────────────────────────────────────

@router.get("/", response_model=list[ShipmentOut])
def list_shipments(db: Session = Depends(get_db)):
    shipments = (
        db.query(Shipment)
        .options(joinedload(Shipment.legs))
        .all()
    )
    return [ShipmentOut.model_validate(s) for s in shipments]
