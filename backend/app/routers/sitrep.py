from fastapi import APIRouter
from pydantic import BaseModel

from app.services.sitrep_parser import parse_sitrep

router = APIRouter(prefix="/api/v1/sitrep", tags=["sitrep"])


# ── Schemas ────────────────────────────────────────────────────────────


class SitrepRequest(BaseModel):
    text: str


class SitrepResponse(BaseModel):
    disaster_type: str
    identified_needs: list[str]
    affected_population: int | None = None
    urgency: str
    summary: str


# ── Endpoints ──────────────────────────────────────────────────────────


@router.post("/parse", response_model=SitrepResponse)
def parse_sitrep_endpoint(req: SitrepRequest):
    result = parse_sitrep(req.text)
    return SitrepResponse(**result)
