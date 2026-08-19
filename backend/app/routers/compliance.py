from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Any

from app.database import get_db
from app.services.compliance import check_compliance

router = APIRouter(prefix="/api/v1/compliance", tags=["compliance"])


# ── Schemas ────────────────────────────────────────────────────────────

class SphereCheck(BaseModel):
    standard: str
    description: str
    status: str
    current_value: float
    target_value: float


class InventoryHealth(BaseModel):
    total_items: int
    items_expiring_30_days: int
    items_expiring_90_days: int
    stockout_risk_count: int


class OperationalMetrics(BaseModel):
    avg_request_fulfillment_days: float
    requests_overdue: int
    delivery_success_rate: float


class ComplianceResult(BaseModel):
    sphere_standards: list[SphereCheck]
    inventory_health: InventoryHealth
    operational_metrics: OperationalMetrics
    overall_score: float


# ── Endpoints ──────────────────────────────────────────────────────────

@router.get("", response_model=ComplianceResult)
def get_compliance(db: Session = Depends(get_db)):
    result = check_compliance(db)
    return ComplianceResult(**result)
