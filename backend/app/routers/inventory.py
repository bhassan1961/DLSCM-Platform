from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.inventory import Warehouse, Item, Stock

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])


# ── Schemas ────────────────────────────────────────────────────────────

class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: str
    category: str
    unit: str
    weight_kg: float
    volume_m3: float


class StockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    warehouse_id: int
    item_id: int
    quantity: int
    lot_number: Optional[str] = None
    expiry_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    item: Optional[ItemOut] = None


class StockUpdate(BaseModel):
    quantity: Optional[int] = None
    lot_number: Optional[str] = None
    expiry_date: Optional[datetime] = None


class WarehouseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: str
    latitude: float
    longitude: float
    capacity_m3: float
    organization_id: int
    stock_count: int = 0


# ── Endpoints ──────────────────────────────────────────────────────────

@router.get("/warehouses", response_model=list[WarehouseOut])
def list_warehouses(db: Session = Depends(get_db)):
    warehouses = db.query(Warehouse).options(joinedload(Warehouse.stocks)).all()
    return [
        WarehouseOut(
            id=w.id, name=w.name, location=w.location,
            latitude=w.latitude, longitude=w.longitude,
            capacity_m3=w.capacity_m3, organization_id=w.organization_id,
            stock_count=len(w.stocks),
        )
        for w in warehouses
    ]


@router.get("/warehouses/{warehouse_id}/stock", response_model=list[StockOut])
def get_warehouse_stock(warehouse_id: int, db: Session = Depends(get_db)):
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    stocks = (
        db.query(Stock)
        .options(joinedload(Stock.item))
        .filter(Stock.warehouse_id == warehouse_id)
        .all()
    )
    return [StockOut.model_validate(s) for s in stocks]


@router.patch("/stock/{stock_id}", response_model=StockOut)
def update_stock(stock_id: int, update: StockUpdate, db: Session = Depends(get_db)):
    stock = (
        db.query(Stock)
        .options(joinedload(Stock.item))
        .filter(Stock.id == stock_id)
        .first()
    )
    if not stock:
        raise HTTPException(status_code=404, detail="Stock record not found")
    if update.quantity is not None:
        stock.quantity = update.quantity
    if update.lot_number is not None:
        stock.lot_number = update.lot_number
    if update.expiry_date is not None:
        stock.expiry_date = update.expiry_date
    db.commit()
    db.refresh(stock)
    return StockOut.model_validate(stock)


@router.get("/items", response_model=list[ItemOut])
def list_items(db: Session = Depends(get_db)):
    items = db.query(Item).all()
    return [ItemOut.model_validate(i) for i in items]


@router.get("/stock", response_model=list[StockOut])
def list_all_stock(
    category: Optional[str] = Query(None, description="Filter by item category"),
    db: Session = Depends(get_db),
):
    query = db.query(Stock).options(joinedload(Stock.item))
    if category:
        query = query.join(Item).filter(Item.category == category)
    stocks = query.all()
    return [StockOut.model_validate(s) for s in stocks]
