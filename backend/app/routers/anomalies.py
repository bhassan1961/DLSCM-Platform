from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app.models.inventory import Warehouse, Stock, Item
from app.models.shipment import Shipment
from app.services.anomaly_detection import (
    detect_inventory_anomalies,
    detect_shipment_anomalies,
    detect_consumption_drift,
)

router = APIRouter(prefix="/api/v1/anomalies", tags=["anomalies"])


@router.get("/inventory")
def get_inventory_anomalies(db: Session = Depends(get_db)):
    stocks = (
        db.query(Stock, Item, Warehouse)
        .join(Item, Stock.item_id == Item.id)
        .join(Warehouse, Stock.warehouse_id == Warehouse.id)
        .all()
    )

    records = []
    now = datetime.now(timezone.utc)
    for stock, item, warehouse in stocks:
        updated = stock.last_updated
        days_since = 0
        if updated:
            try:
                days_since = (now - updated.replace(tzinfo=timezone.utc)).days
            except Exception:
                days_since = 0

        min_req = max(10, stock.quantity // 2) if stock.quantity > 0 else 10
        records.append({
            "warehouse_id": warehouse.id,
            "warehouse_name": warehouse.name,
            "item_id": item.id,
            "item_name": item.name,
            "category": item.category,
            "quantity": stock.quantity,
            "min_required": min_req,
            "days_since_update": days_since,
        })

    return detect_inventory_anomalies(records)


@router.get("/shipments")
def get_shipment_anomalies(db: Session = Depends(get_db)):
    shipments = db.query(Shipment).all()

    records = []
    now = datetime.now(timezone.utc)
    for s in shipments:
        est_days = 7
        actual_days = est_days
        if s.departed_at and s.eta:
            est_days = max(1, (s.eta - s.departed_at).days)
        if s.departed_at and s.delivered_at:
            actual_days = max(1, (s.delivered_at - s.departed_at).days)
        elif s.departed_at:
            actual_days = max(1, (now - s.departed_at.replace(tzinfo=timezone.utc)).days)
        else:
            actual_days = est_days

        delay = max(0, actual_days - est_days)
        origin_name = s.origin_warehouse.name if s.origin_warehouse else "Unknown"
        dest = s.request.destination_name if s.request else "Unknown"
        items_count = len(s.request.items) if s.request and s.request.items else 1

        records.append({
            "id": s.id,
            "tracking_id": s.tracking_id,
            "status": s.status,
            "origin": origin_name,
            "destination": dest,
            "estimated_days": est_days,
            "actual_days": actual_days,
            "delay_days": delay,
            "items_count": items_count,
        })

    return detect_shipment_anomalies(records)


@router.get("/consumption-drift")
def get_consumption_drift(db: Session = Depends(get_db)):
    stocks = db.query(Stock).order_by(Stock.last_updated).all()
    if not stocks:
        return {"drift_detected": False, "reason": "no_stock_data"}

    quantities = [float(s.quantity) for s in stocks]
    window = max(1, min(7, len(quantities) // 2))
    return detect_consumption_drift(quantities, window=window)


@router.get("/summary")
def get_anomaly_summary(db: Session = Depends(get_db)):
    inv = get_inventory_anomalies(db)
    ship = get_shipment_anomalies(db)
    drift = get_consumption_drift(db)

    inv_critical = sum(1 for a in inv.get("anomalies", []) if a.get("severity") == "critical")
    ship_critical = sum(1 for a in ship.get("anomalies", []) if a.get("severity") == "critical")

    return {
        "inventory": {
            "total_anomalies": len(inv.get("anomalies", [])),
            "critical": inv_critical,
            "method": inv.get("summary", {}).get("method", "unknown"),
        },
        "shipments": {
            "total_anomalies": len(ship.get("anomalies", [])),
            "critical": ship_critical,
            "method": ship.get("summary", {}).get("method", "unknown"),
        },
        "consumption_drift": drift,
    }
