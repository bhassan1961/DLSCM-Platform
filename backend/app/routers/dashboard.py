from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.alert import Alert
from app.models.disaster import Disaster
from app.models.inventory import Stock, Warehouse
from app.models.shipment import Shipment
from app.models.supply_request import SupplyRequest
from app.models.user import Organization

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


# ── Schemas ────────────────────────────────────────────────────────────


class DashboardStats(BaseModel):
    active_disasters: int
    total_warehouses: int
    pending_requests: int
    in_transit_shipments: int
    active_alerts: int
    total_organizations: int
    total_stock_items: int
    affected_population: int


# ── Endpoints ──────────────────────────────────────────────────────────


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    active_disasters = db.query(Disaster).filter(Disaster.status == "active").count()
    total_warehouses = db.query(Warehouse).count()
    pending_requests = (
        db.query(SupplyRequest).filter(SupplyRequest.status == "pending").count()
    )
    in_transit_shipments = (
        db.query(Shipment).filter(Shipment.status == "in_transit").count()
    )
    active_alerts = db.query(Alert).filter(Alert.status == "active").count()
    total_organizations = db.query(Organization).count()
    total_stock_items = db.query(func.coalesce(func.sum(Stock.quantity), 0)).scalar()
    affected_population = (
        db.query(func.coalesce(func.sum(Disaster.affected_population), 0))
        .filter(Disaster.status == "active")
        .scalar()
    )

    return DashboardStats(
        active_disasters=active_disasters,
        total_warehouses=total_warehouses,
        pending_requests=pending_requests,
        in_transit_shipments=in_transit_shipments,
        active_alerts=active_alerts,
        total_organizations=total_organizations,
        total_stock_items=total_stock_items,
        affected_population=affected_population,
    )
