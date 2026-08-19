from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.disaster import Disaster
from app.models.supplier import Supplier
from app.services.forecasting import forecast_demand
from app.services.risk_model import calculate_risk, RISK_PROFILES
from app.services.disruption import predict_disruptions

router = APIRouter(prefix="/api/v1/forecasting", tags=["forecasting"])


# ── Schemas ────────────────────────────────────────────────────────────

class CategoryForecast(BaseModel):
    total: float
    daily: list[float]
    unit: str
    description: str
    confidence_lower: Optional[list[float]] = None
    confidence_upper: Optional[list[float]] = None
    model: Optional[str] = None
    decomposition: Optional[dict] = None
    feature_importances: Optional[dict] = None
    cross_model_inputs: Optional[dict] = None


class ForecastResponse(BaseModel):
    disaster_id: int
    disaster_name: str
    disaster_type: str
    severity: str
    affected_population: int
    days_ahead: int
    forecasts: dict[str, CategoryForecast]
    cross_model_context: Optional[dict] = None


def _get_risk_context(disaster_region: str) -> dict:
    best_match = None
    best_score = 0
    region_lower = disaster_region.lower() if disaster_region else ""
    for key in RISK_PROFILES:
        profile = RISK_PROFILES[key]
        name_lower = profile["name"].lower()
        if region_lower in name_lower or name_lower in region_lower:
            result = calculate_risk(key)
            if result.get("composite_score", 0) > best_score:
                best_score = result["composite_score"]
                best_match = result
    if not best_match and RISK_PROFILES:
        first_key = next(iter(RISK_PROFILES))
        best_match = calculate_risk(first_key)
    return best_match or {}


def _get_disruption_context(db: Session) -> dict:
    suppliers = db.query(Supplier).all()
    if not suppliers:
        return {}
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


# ── Endpoints ──────────────────────────────────────────────────────────

@router.get("/{disaster_id}")
def get_forecast(
    disaster_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    disaster = db.query(Disaster).filter(Disaster.id == disaster_id).first()
    if not disaster:
        raise HTTPException(status_code=404, detail="Disaster not found")

    risk_ctx = _get_risk_context(disaster.region or disaster.country or disaster.name)
    disruption_ctx = _get_disruption_context(db)

    raw = forecast_demand(
        disaster_type=disaster.disaster_type,
        severity=disaster.severity,
        affected_population=disaster.affected_population,
        days_ahead=days,
        risk_context=risk_ctx,
        disruption_context=disruption_ctx,
    )

    forecasts = {k: CategoryForecast(**v) for k, v in raw.items()}

    return {
        "disaster_id": disaster.id,
        "disaster_name": disaster.name,
        "disaster_type": disaster.disaster_type,
        "severity": disaster.severity,
        "affected_population": disaster.affected_population,
        "days_ahead": days,
        "forecasts": {k: v.model_dump() for k, v in forecasts.items()},
        "cross_model_context": {
            "risk_region": risk_ctx.get("region_name") if risk_ctx else None,
            "risk_score": risk_ctx.get("composite_score") if risk_ctx else None,
            "risk_level": risk_ctx.get("risk_level") if risk_ctx else None,
            "supplier_disruption_summary": {
                "total_suppliers": len(disruption_ctx.get("suppliers", [])),
                "high_risk_suppliers": sum(
                    1 for s in disruption_ctx.get("suppliers", [])
                    if s.get("risk_level") in ("critical", "high")
                ),
            } if disruption_ctx else None,
        },
    }
