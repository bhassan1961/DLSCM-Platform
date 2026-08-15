from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.simulation import Scenario
from app.services.forecasting import forecast_demand
from app.services.damage_assessment import assess_damage

router = APIRouter(prefix="/api/v1/simulation", tags=["simulation"])


# ── Schemas ────────────────────────────────────────────────────────────

class ScenarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    disaster_type: str
    severity: str
    country: str
    latitude: float
    longitude: float
    affected_population: int
    parameters: Optional[dict] = None
    results: Optional[dict] = None
    status: str
    created_at: Optional[datetime] = None


class ScenarioCreate(BaseModel):
    name: str
    disaster_type: str
    severity: str
    country: str
    latitude: float
    longitude: float
    affected_population: int
    parameters: Optional[dict] = None


class SimulationRunRequest(BaseModel):
    disaster_type: str
    severity: str
    affected_population: int
    days_ahead: int = 30


class SimulationResult(BaseModel):
    demand_forecast: dict
    damage_assessment: dict
    estimated_response_cost_usd: float
    estimated_response_hours: float
    nearest_warehouse_km: float
    readiness_score: float
    recommended_prepositioning: dict


# ── Endpoints ──────────────────────────────────────────────────────────

@router.post("/run", response_model=SimulationResult)
def run_simulation(req: SimulationRunRequest):
    demand = forecast_demand(
        disaster_type=req.disaster_type,
        severity=req.severity,
        affected_population=req.affected_population,
        days_ahead=req.days_ahead,
    )

    damage = assess_damage(
        disaster_type=req.disaster_type,
        severity=req.severity,
    )

    # Estimate response cost based on affected population and severity
    severity_cost_multiplier = {
        "minor": 15,
        "moderate": 35,
        "major": 65,
        "catastrophic": 120,
    }
    cost_per_person = severity_cost_multiplier.get(req.severity, 50)
    estimated_cost = req.affected_population * cost_per_person

    # Summary of recommended prepositioning
    food_total = demand.get("food", {}).get("total", 0)
    water_total = demand.get("water", {}).get("total", 0)
    medical_total = demand.get("medical", {}).get("total", 0)
    shelter_total = demand.get("shelter", {}).get("total", 0)

    recommended = {
        "food_kg": round(food_total),
        "water_liters": round(water_total),
        "medical_treatments": round(medical_total),
        "shelter_units": round(shelter_total),
        "buffer_percentage": 20,
        "note": "Includes 20% buffer above forecast demand",
    }

    severity_speed_factor = {"minor": 1.0, "moderate": 1.3, "major": 1.8, "catastrophic": 2.5}
    base_hours = 24 * severity_speed_factor.get(req.severity, 1.5)
    nearest_km = 350 * severity_speed_factor.get(req.severity, 1.5)
    readiness = max(0, 100 - damage.get("overall_damage_index", 50) * 0.8)

    return SimulationResult(
        demand_forecast=demand,
        damage_assessment=damage,
        estimated_response_cost_usd=estimated_cost,
        estimated_response_hours=round(base_hours, 1),
        nearest_warehouse_km=round(nearest_km, 0),
        readiness_score=round(readiness, 1),
        recommended_prepositioning=recommended,
    )


@router.get("/scenarios", response_model=list[ScenarioOut])
def list_scenarios(db: Session = Depends(get_db)):
    scenarios = db.query(Scenario).all()
    return [ScenarioOut.model_validate(s) for s in scenarios]


@router.post("/scenarios", response_model=ScenarioOut)
def create_scenario(req: ScenarioCreate, db: Session = Depends(get_db)):
    scenario = Scenario(
        name=req.name,
        disaster_type=req.disaster_type,
        severity=req.severity,
        country=req.country,
        latitude=req.latitude,
        longitude=req.longitude,
        affected_population=req.affected_population,
        parameters=req.parameters,
        status="draft",
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return ScenarioOut.model_validate(scenario)
