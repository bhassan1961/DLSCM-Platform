from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.supplier import Supplier
from app.services.disruption import predict_disruptions

router = APIRouter(prefix="/api/v1/suppliers", tags=["suppliers"])


# ── Schemas ────────────────────────────────────────────────────────────

class SupplierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    country: str
    contact_email: Optional[str] = None
    lead_time_days: Optional[int] = None
    quality_rating: Optional[float] = None
    capacity_description: Optional[str] = None
    pre_qualified: bool = False
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


class SupplierCreate(BaseModel):
    name: str
    category: str
    country: str
    contact_email: Optional[str] = None
    lead_time_days: Optional[int] = None
    quality_rating: Optional[float] = None
    capacity_description: Optional[str] = None
    pre_qualified: bool = False
    notes: Optional[str] = None


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    country: Optional[str] = None
    contact_email: Optional[str] = None
    lead_time_days: Optional[int] = None
    quality_rating: Optional[float] = None
    capacity_description: Optional[str] = None
    pre_qualified: Optional[bool] = None
    notes: Optional[str] = None


VALID_CATEGORIES = {"food", "medical", "shelter", "logistics", "water", "nfi", "general"}


# ── Endpoints ──────────────────────────────────────────────────────────

@router.get("", response_model=list[SupplierOut])
def list_suppliers(
    category: Optional[str] = Query(None, description="Filter by supplier category"),
    db: Session = Depends(get_db),
):
    query = db.query(Supplier)
    if category:
        query = query.filter(Supplier.category == category)
    suppliers = query.all()
    return [SupplierOut.model_validate(s) for s in suppliers]


@router.post("", response_model=SupplierOut)
def create_supplier(supplier: SupplierCreate, db: Session = Depends(get_db)):
    if supplier.category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of: {VALID_CATEGORIES}")
    s = Supplier(**supplier.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return SupplierOut.model_validate(s)


@router.patch("/{supplier_id}", response_model=SupplierOut)
def update_supplier(supplier_id: int, update: SupplierUpdate, db: Session = Depends(get_db)):
    s = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")
    update_data = update.model_dump(exclude_unset=True)
    if "category" in update_data and update_data["category"] not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of: {VALID_CATEGORIES}")
    for key, value in update_data.items():
        setattr(s, key, value)
    db.commit()
    db.refresh(s)
    return SupplierOut.model_validate(s)


@router.get("/disruptions")
def get_disruption_predictions(db: Session = Depends(get_db)):
    suppliers = db.query(Supplier).all()
    if not suppliers:
        return {"suppliers": [], "model_info": {"algorithm": "none", "note": "No suppliers in database"}}
    supplier_data = [
        {
            "id": s.id,
            "name": s.name,
            "lead_time_days": s.lead_time_days or 14,
            "quality_rating": s.quality_rating or 3.0,
            "on_time_rate": 0.85,
            "capacity_utilization": 0.6,
            "defect_rate": 0.02,
            "price_volatility": 0.1,
        }
        for s in suppliers
    ]
    return predict_disruptions(supplier_data)
