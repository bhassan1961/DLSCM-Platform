import math
import os

import httpx

OSRM_BASE_URL = os.getenv("OSRM_URL", "https://router.project-osrm.org")

MODE_SPEEDS = {
    "road": 45,
    "air": 650,
    "sea": 30,
    "rail": 80,
}

CONDITION_PENALTIES = {
    "flooding": 2.5,
    "conflict": 5.0,
    "road_damage": 3.0,
    "checkpoint": 1.5,
    "port_congestion": 2.0,
    "weather": 1.8,
}

# Active route conditions (would be populated from alerts/intelligence in production)
ACTIVE_CONDITIONS = [
    {
        "id": "cond-1",
        "type": "flooding",
        "latitude": 21.4272,
        "longitude": 92.0058,
        "radius_km": 50,
        "description": "Monsoon flooding - Cox's Bazar roads impassable",
        "severity": "severe",
        "modes_affected": ["road", "rail"],
    },
    {
        "id": "cond-2",
        "type": "conflict",
        "latitude": 36.2021,
        "longitude": 37.1343,
        "radius_km": 80,
        "description": "Security corridor - Armed escort required for Aleppo route",
        "severity": "high",
        "modes_affected": ["road"],
    },
    {
        "id": "cond-3",
        "type": "port_congestion",
        "latitude": -4.0435,
        "longitude": 39.6682,
        "radius_km": 20,
        "description": "Mombasa port congestion - 8 day clearance delays",
        "severity": "moderate",
        "modes_affected": ["sea"],
    },
    {
        "id": "cond-4",
        "type": "road_damage",
        "latitude": -19.8436,
        "longitude": 34.8389,
        "radius_km": 40,
        "description": "Cyclone damage - Beira access roads partially destroyed",
        "severity": "severe",
        "modes_affected": ["road"],
    },
]


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _check_conditions(
    lat1: float, lng1: float, lat2: float, lng2: float, mode: str
) -> list:
    """Check which active conditions affect a leg."""
    affected = []
    for cond in ACTIVE_CONDITIONS:
        if mode not in cond["modes_affected"]:
            continue
        mid_lat = (lat1 + lat2) / 2
        mid_lng = (lng1 + lng2) / 2
        dist = haversine(mid_lat, mid_lng, cond["latitude"], cond["longitude"])
        if dist <= cond["radius_km"]:
            affected.append(cond)
        dist_from = haversine(lat1, lng1, cond["latitude"], cond["longitude"])
        dist_to = haversine(lat2, lng2, cond["latitude"], cond["longitude"])
        if (
            dist_from <= cond["radius_km"] or dist_to <= cond["radius_km"]
        ) and cond not in affected:
            affected.append(cond)
    return affected


async def _osrm_route(
    origin: dict, destination: dict, waypoints: list | None = None
) -> dict | None:
    """Fetch a road route from OSRM public API."""
    coords = [f"{origin['lng']},{origin['lat']}"]
    if waypoints:
        for wp in waypoints:
            coords.append(f"{wp['lng']},{wp['lat']}")
    coords.append(f"{destination['lng']},{destination['lat']}")
    coords_str = ";".join(coords)

    url = f"{OSRM_BASE_URL}/route/v1/driving/{coords_str}"
    params = {"overview": "full", "geometries": "geojson", "steps": "true"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == "Ok" and data.get("routes"):
                    route = data["routes"][0]
                    return {
                        "distance_m": route["distance"],
                        "duration_s": route["duration"],
                        "geometry": route["geometry"],
                        "legs": route.get("legs", []),
                    }
    except (httpx.HTTPError, httpx.TimeoutException):
        pass
    return None


async def optimize_route_async(
    origin: dict,
    destination: dict,
    mode: str = "road",
    waypoints: list | None = None,
    avoid_conditions: bool = True,
) -> dict:
    """Enhanced route optimization with OSRM and condition awareness."""

    # Try OSRM for road routing
    osrm_data = None
    if mode == "road":
        osrm_data = await _osrm_route(origin, destination, waypoints)

    points = [origin]
    if waypoints:
        points.extend(waypoints)
    points.append(destination)

    speed = MODE_SPEEDS.get(mode, 45)
    legs = []
    total_distance = 0.0
    total_duration = 0.0
    route_conditions = []
    routing_source = "haversine"

    if osrm_data and mode == "road":
        routing_source = "osrm"
        osrm_legs = osrm_data.get("legs", [])

        for i, osrm_leg in enumerate(osrm_legs):
            p1 = points[i] if i < len(points) else points[-2]
            p2 = points[i + 1] if i + 1 < len(points) else points[-1]

            distance_km = osrm_leg["distance"] / 1000.0
            duration_hours = osrm_leg["duration"] / 3600.0

            conditions = _check_conditions(
                p1["lat"], p1["lng"], p2["lat"], p2["lng"], mode
            )
            condition_delay = 0.0
            leg_warnings = []
            for c in conditions:
                penalty = CONDITION_PENALTIES.get(c["type"], 1.0)
                condition_delay += penalty
                leg_warnings.append(
                    {
                        "id": c["id"],
                        "type": c["type"],
                        "description": c["description"],
                        "severity": c["severity"],
                        "delay_hours": penalty,
                    }
                )
                if c not in route_conditions:
                    route_conditions.append(c)

            duration_hours += condition_delay

            legs.append(
                {
                    "leg_order": i + 1,
                    "from": {"lat": p1["lat"], "lng": p1["lng"]},
                    "to": {"lat": p2["lat"], "lng": p2["lng"]},
                    "mode": mode,
                    "distance_km": round(distance_km, 1),
                    "duration_hours": round(duration_hours, 2),
                    "conditions": leg_warnings,
                }
            )
            total_distance += distance_km
            total_duration += duration_hours
    else:
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]

            distance = haversine(p1["lat"], p1["lng"], p2["lat"], p2["lng"])
            if mode in ("road", "rail"):
                distance *= 1.3

            duration = distance / speed

            conditions = _check_conditions(
                p1["lat"], p1["lng"], p2["lat"], p2["lng"], mode
            )
            condition_delay = 0.0
            leg_warnings = []
            for c in conditions:
                penalty = CONDITION_PENALTIES.get(c["type"], 1.0)
                condition_delay += penalty
                leg_warnings.append(
                    {
                        "id": c["id"],
                        "type": c["type"],
                        "description": c["description"],
                        "severity": c["severity"],
                        "delay_hours": penalty,
                    }
                )
                if c not in route_conditions:
                    route_conditions.append(c)

            duration += condition_delay

            legs.append(
                {
                    "leg_order": i + 1,
                    "from": {"lat": p1["lat"], "lng": p1["lng"]},
                    "to": {"lat": p2["lat"], "lng": p2["lng"]},
                    "mode": mode,
                    "distance_km": round(distance, 1),
                    "duration_hours": round(duration, 2),
                    "conditions": leg_warnings,
                }
            )
            total_distance += distance
            total_duration += duration

    return {
        "legs": legs,
        "total_distance_km": round(total_distance, 1),
        "total_duration_hours": round(total_duration, 2),
        "mode": mode,
        "routing_source": routing_source,
        "conditions_on_route": [
            {
                "id": c["id"],
                "type": c["type"],
                "description": c["description"],
                "severity": c["severity"],
                "location": {"lat": c["latitude"], "lng": c["longitude"]},
            }
            for c in route_conditions
        ],
    }


def optimize_route(
    origin: dict,
    destination: dict,
    mode: str = "road",
    waypoints: list | None = None,
) -> dict:
    """Synchronous fallback for backward compatibility."""
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Inside an async context — use haversine-only path
        return _sync_optimize(origin, destination, mode, waypoints)
    return asyncio.run(optimize_route_async(origin, destination, mode, waypoints))


def _sync_optimize(origin, destination, mode, waypoints):
    speed = MODE_SPEEDS.get(mode, 45)
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
        if mode in ("road", "rail"):
            distance *= 1.3
        duration = distance / speed
        legs.append(
            {
                "leg_order": i + 1,
                "from": {"lat": p1["lat"], "lng": p1["lng"]},
                "to": {"lat": p2["lat"], "lng": p2["lng"]},
                "mode": mode,
                "distance_km": round(distance, 1),
                "duration_hours": round(duration, 2),
            }
        )
        total_distance += distance
        total_duration += duration

    return {
        "legs": legs,
        "total_distance_km": round(total_distance, 1),
        "total_duration_hours": round(total_duration, 2),
        "mode": mode,
    }


def get_active_conditions() -> list:
    return [
        {
            "id": c["id"],
            "type": c["type"],
            "description": c["description"],
            "severity": c["severity"],
            "location": {"lat": c["latitude"], "lng": c["longitude"]},
            "radius_km": c["radius_km"],
            "modes_affected": c["modes_affected"],
        }
        for c in ACTIVE_CONDITIONS
    ]
