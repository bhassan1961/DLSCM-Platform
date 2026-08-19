from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.routing import optimize_route_async, get_active_conditions

router = APIRouter(prefix="/api/v1/routing", tags=["routing"])


# ── Schemas ────────────────────────────────────────────────────────────

class LatLng(BaseModel):
    lat: float
    lng: float


class RouteRequest(BaseModel):
    origin: LatLng
    destination: LatLng
    mode: str = "road"
    waypoints: Optional[list[LatLng]] = None
    avoid_conditions: bool = True


# ── Endpoints ──────────────────────────────────────────────────────────

@router.post("/optimize")
async def route_optimize(req: RouteRequest):
    origin = {"lat": req.origin.lat, "lng": req.origin.lng}
    destination = {"lat": req.destination.lat, "lng": req.destination.lng}
    waypoints = None
    if req.waypoints:
        waypoints = [{"lat": wp.lat, "lng": wp.lng} for wp in req.waypoints]

    result = await optimize_route_async(
        origin, destination,
        mode=req.mode,
        waypoints=waypoints,
        avoid_conditions=req.avoid_conditions,
    )
    return result


@router.get("/conditions")
def list_conditions():
    return {"conditions": get_active_conditions()}
