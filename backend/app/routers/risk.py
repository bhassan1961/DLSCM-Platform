from fastapi import APIRouter
from pydantic import BaseModel

from app.services.risk_model import RISK_PROFILES, calculate_risk

router = APIRouter(prefix="/api/v1/risk", tags=["risk"])


# ── Schemas ────────────────────────────────────────────────────────────


class RiskRegion(BaseModel):
    region: str
    region_name: str
    latitude: float
    longitude: float
    composite_score: float
    risk_level: str
    components: dict
    hazard_breakdown: dict
    dominant_hazard: str


class RiskMapResponse(BaseModel):
    regions: list[RiskRegion]


# ── Endpoints ──────────────────────────────────────────────────────────


@router.get("/map", response_model=RiskMapResponse)
def get_risk_map():
    regions = []
    for region_key in RISK_PROFILES:
        result = calculate_risk(region_key)
        if "error" not in result:
            regions.append(RiskRegion(**result))
    regions.sort(key=lambda r: r.composite_score, reverse=True)
    return RiskMapResponse(regions=regions)
