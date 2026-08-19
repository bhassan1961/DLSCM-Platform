from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.supply_request import SupplyRequest, RequestItem
from app.models.user import User
from app.models.inventory import Item

router = APIRouter(prefix="/api/v1/requests", tags=["supply_requests"])


class RequestItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: int
    item_id: int
    item_name: str = ""
    quantity_requested: int
    quantity_fulfilled: int


class RequestItemCreate(BaseModel):
    item_id: int
    quantity_requested: int


class SupplyRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: str
    priority: str
    disaster_id: Optional[int] = None
    requester_id: int
    requester_name: str = ""
    destination_lat: Optional[float] = None
    destination_lng: Optional[float] = None
    destination_name: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: list[RequestItemOut] = []


class SupplyRequestCreate(BaseModel):
    title: str
    priority: str = "medium"
    disaster_id: Optional[int] = None
    requester_id: int
    destination_lat: Optional[float] = None
    destination_lng: Optional[float] = None
    destination_name: Optional[str] = None
    notes: Optional[str] = None
    items: list[RequestItemCreate] = []


class StatusUpdate(BaseModel):
    status: str


VALID_STATUSES = {"pending", "approved", "sourcing", "dispatched", "delivered", "cancelled"}


def _to_out(sr: SupplyRequest) -> SupplyRequestOut:
    items_out = []
    for ri in sr.items:
        items_out.append(RequestItemOut(
            id=ri.id, request_id=ri.request_id, item_id=ri.item_id,
            item_name=ri.item.name if ri.item else "",
            quantity_requested=ri.quantity_requested,
            quantity_fulfilled=ri.quantity_fulfilled,
        ))
    return SupplyRequestOut(
        id=sr.id, title=sr.title, status=sr.status, priority=sr.priority,
        disaster_id=sr.disaster_id, requester_id=sr.requester_id,
        requester_name=sr.requester.name if sr.requester else "",
        destination_lat=sr.destination_lat, destination_lng=sr.destination_lng,
        destination_name=sr.destination_name, notes=sr.notes,
        created_at=sr.created_at, updated_at=sr.updated_at,
        items=items_out,
    )


def _eager_query(db: Session):
    return db.query(SupplyRequest).options(
        joinedload(SupplyRequest.items).joinedload(RequestItem.item),
        joinedload(SupplyRequest.requester),
    )


@router.get("", response_model=list[SupplyRequestOut])
def list_requests(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = _eager_query(db)
    if status:
        q = q.filter(SupplyRequest.status == status)
    requests = q.order_by(SupplyRequest.created_at.desc()).all()
    return [_to_out(r) for r in requests]


@router.post("", response_model=SupplyRequestOut)
def create_request(req: SupplyRequestCreate, db: Session = Depends(get_db)):
    sr = SupplyRequest(
        title=req.title, priority=req.priority,
        disaster_id=req.disaster_id, requester_id=req.requester_id,
        destination_lat=req.destination_lat, destination_lng=req.destination_lng,
        destination_name=req.destination_name, notes=req.notes,
    )
    db.add(sr)
    db.flush()
    for item_data in req.items:
        db.add(RequestItem(
            request_id=sr.id, item_id=item_data.item_id,
            quantity_requested=item_data.quantity_requested, quantity_fulfilled=0,
        ))
    db.commit()
    result = _eager_query(db).filter(SupplyRequest.id == sr.id).first()
    return _to_out(result)


@router.patch("/{request_id}/status", response_model=SupplyRequestOut)
def update_request_status(request_id: int, update: StatusUpdate, db: Session = Depends(get_db)):
    if update.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {VALID_STATUSES}")
    sr = _eager_query(db).filter(SupplyRequest.id == request_id).first()
    if not sr:
        raise HTTPException(status_code=404, detail="Supply request not found")
    sr.status = update.status
    db.commit()
    db.refresh(sr)
    return _to_out(sr)
