from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.disaster import Disaster
from app.services.forecasting import forecast_demand

router = APIRouter(prefix="/api/v1/forecasting", tags=["forecasting"])


# ── Schemas ────────────────────────────────────────────────────────────

class CategoryForecast(BaseModel):
    total: float
    daily: list[float]
    unit: str
    description: str


class ForecastResponse(BaseModel):
    disaster_id: int
    disaster_name: str
    disaster_type: str
    severity: str
    affected_population: int
    days_ahead: int
    forecasts: dict[str, CategoryForecast]


# ── Endpoints ──────────────────────────────────────────────────────────

@router.get("/{disaster_id}", response_model=ForecastResponse)
def get_forecast(
    disaster_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    disaster = db.query(Disaster).filter(Disaster.id == disaster_id).first()
    if not disaster:
        raise HTTPException(status_code=404, detail="Disaster not found")

    raw = forecast_demand(
        disaster_type=disaster.disaster_type,
        severity=disaster.severity,
        affected_population=disaster.affected_population,
        days_ahead=days,
    )

    forecasts = {k: CategoryForecast(**v) for k, v in raw.items()}

    return ForecastResponse(
        disaster_id=disaster.id,
        disaster_name=disaster.name,
        disaster_type=disaster.disaster_type,
        severity=disaster.severity,
        affected_population=disaster.affected_population,
        days_ahead=days,
        forecasts=forecasts,
    )
