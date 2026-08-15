import math
from typing import Optional


# Average speeds by transport mode (km/h)
MODE_SPEEDS = {
    "road": 45,
    "air": 650,
    "sea": 30,
    "rail": 80,
}


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in km."""
    R = 6371.0  # Earth radius in km
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def optimize_route(
    origin: dict,
    destination: dict,
    mode: str = "road",
    waypoints: Optional[list] = None,
) -> dict:
    """
    Calculate a route from origin to destination with optional waypoints.

    origin/destination: {"lat": float, "lng": float}
    waypoints: list of {"lat": float, "lng": float}
    mode: "road", "air", "sea", or "rail"

    Returns dict with legs, total_distance_km, total_duration_hours.
    """
    speed = MODE_SPEEDS.get(mode, 45)

    # Build ordered list of points
    points = [origin]
    if waypoints:
        points.extend(waypoints)
    points.append(destination)

    legs = []
    total_distance = 0.0
    total_duration = 0.0

    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i + 1]

        distance = haversine(p1["lat"], p1["lng"], p2["lat"], p2["lng"])

        # For road/rail, add 30% to account for non-straight routes
        if mode in ("road", "rail"):
            distance *= 1.3

        duration = distance / speed

        legs.append({
            "leg_order": i + 1,
            "from": {"lat": p1["lat"], "lng": p1["lng"]},
            "to": {"lat": p2["lat"], "lng": p2["lng"]},
            "mode": mode,
            "distance_km": round(distance, 1),
            "duration_hours": round(duration, 2),
        })

        total_distance += distance
        total_duration += duration

    return {
        "legs": legs,
        "total_distance_km": round(total_distance, 1),
        "total_duration_hours": round(total_duration, 2),
        "mode": mode,
    }
