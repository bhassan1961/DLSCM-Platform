from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.routing import optimize_route

router = APIRouter(prefix="/api/v1/routing", tags=["routing"])


# ── Schemas ────────────────────────────────────────────────────────────

class LatLng(BaseModel):
    lat: float
    lng: float


class RouteLeg(BaseModel):
    leg_order: int
    from_point: dict  # {"lat": float, "lng": float} serialized from "from"
    to_point: dict
    mode: str
    distance_km: float
    duration_hours: float


class RouteRequest(BaseModel):
    origin: LatLng
    destination: LatLng
    mode: str = "road"
    waypoints: Optional[list[LatLng]] = None


class RouteResponse(BaseModel):
    legs: list[dict]
    total_distance_km: float
    total_duration_hours: float
    mode: str


# ── Endpoints ──────────────────────────────────────────────────────────

@router.post("/optimize", response_model=RouteResponse)
def route_optimize(req: RouteRequest):
    origin = {"lat": req.origin.lat, "lng": req.origin.lng}
    destination = {"lat": req.destination.lat, "lng": req.destination.lng}
    waypoints = None
    if req.waypoints:
        waypoints = [{"lat": wp.lat, "lng": wp.lng} for wp in req.waypoints]

    result = optimize_route(origin, destination, mode=req.mode, waypoints=waypoints)
    return RouteResponse(**result)
