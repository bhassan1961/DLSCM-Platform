"""
Multi-hazard risk scoring model.

Computes a composite risk score combining:
  - Hazard frequency (how often disasters occur)
  - Population exposure (density and vulnerability)
  - Infrastructure vulnerability (capacity to withstand/respond)
"""


# Predefined risk profiles for known regions
RISK_PROFILES = {
    "horn_of_africa": {
        "name": "Horn of Africa",
        "latitude": 2.0,
        "longitude": 40.0,
        "hazards": {
            "drought": {"frequency": 0.85, "typical_severity": "major"},
            "flood": {"frequency": 0.45, "typical_severity": "moderate"},
            "conflict": {"frequency": 0.60, "typical_severity": "major"},
            "epidemic": {"frequency": 0.35, "typical_severity": "moderate"},
        },
        "population_exposure": 0.82,
        "infrastructure_vulnerability": 0.78,
    },
    "south_asia_coast": {
        "name": "South Asia Coastal",
        "latitude": 22.0,
        "longitude": 90.0,
        "hazards": {
            "cyclone": {"frequency": 0.70, "typical_severity": "major"},
            "flood": {"frequency": 0.90, "typical_severity": "catastrophic"},
            "earthquake": {"frequency": 0.25, "typical_severity": "moderate"},
        },
        "population_exposure": 0.95,
        "infrastructure_vulnerability": 0.72,
    },
    "eastern_mediterranean": {
        "name": "Eastern Mediterranean",
        "latitude": 35.0,
        "longitude": 37.0,
        "hazards": {
            "earthquake": {"frequency": 0.55, "typical_severity": "major"},
            "conflict": {"frequency": 0.80, "typical_severity": "catastrophic"},
            "drought": {"frequency": 0.30, "typical_severity": "moderate"},
        },
        "population_exposure": 0.88,
        "infrastructure_vulnerability": 0.65,
    },
    "southeast_africa": {
        "name": "Southeast Africa",
        "latitude": -18.0,
        "longitude": 35.0,
        "hazards": {
            "cyclone": {"frequency": 0.60, "typical_severity": "major"},
            "flood": {"frequency": 0.65, "typical_severity": "major"},
            "drought": {"frequency": 0.40, "typical_severity": "moderate"},
            "epidemic": {"frequency": 0.30, "typical_severity": "moderate"},
        },
        "population_exposure": 0.70,
        "infrastructure_vulnerability": 0.80,
    },
    "central_sahel": {
        "name": "Central Sahel",
        "latitude": 14.0,
        "longitude": 2.0,
        "hazards": {
            "conflict": {"frequency": 0.75, "typical_severity": "major"},
            "drought": {"frequency": 0.70, "typical_severity": "major"},
            "flood": {"frequency": 0.35, "typical_severity": "moderate"},
        },
        "population_exposure": 0.75,
        "infrastructure_vulnerability": 0.85,
    },
    "caribbean": {
        "name": "Caribbean",
        "latitude": 18.0,
        "longitude": -72.0,
        "hazards": {
            "cyclone": {"frequency": 0.75, "typical_severity": "catastrophic"},
            "earthquake": {"frequency": 0.40, "typical_severity": "major"},
            "flood": {"frequency": 0.55, "typical_severity": "moderate"},
        },
        "population_exposure": 0.60,
        "infrastructure_vulnerability": 0.55,
    },
    "central_america": {
        "name": "Central America",
        "latitude": 14.0,
        "longitude": -87.0,
        "hazards": {
            "cyclone": {"frequency": 0.55, "typical_severity": "major"},
            "earthquake": {"frequency": 0.45, "typical_severity": "moderate"},
            "flood": {"frequency": 0.60, "typical_severity": "major"},
            "drought": {"frequency": 0.35, "typical_severity": "moderate"},
        },
        "population_exposure": 0.65,
        "infrastructure_vulnerability": 0.60,
    },
    "pacific_islands": {
        "name": "Pacific Islands",
        "latitude": -15.0,
        "longitude": 170.0,
        "hazards": {
            "cyclone": {"frequency": 0.80, "typical_severity": "catastrophic"},
            "earthquake": {"frequency": 0.50, "typical_severity": "major"},
            "flood": {"frequency": 0.40, "typical_severity": "moderate"},
        },
        "population_exposure": 0.50,
        "infrastructure_vulnerability": 0.70,
    },
}


def calculate_risk(region: str) -> dict:
    """
    Calculate composite multi-hazard risk score for a region.

    The composite score combines:
      - Aggregate hazard score (weighted sum of frequency * severity_weight)
      - Population exposure factor
      - Infrastructure vulnerability factor

    Returns dict with composite_score, component breakdown, and risk_level.
    """
    profile = RISK_PROFILES.get(region)
    if not profile:
        return {"error": f"Unknown region: {region}", "available_regions": list(RISK_PROFILES.keys())}

    severity_weights = {
        "minor": 0.25,
        "moderate": 0.50,
        "major": 0.75,
        "catastrophic": 1.0,
    }

    # Calculate aggregate hazard score (0-100)
    hazard_scores = {}
    total_hazard = 0
    for hazard, info in profile["hazards"].items():
        sev_weight = severity_weights.get(info["typical_severity"], 0.5)
        score = info["frequency"] * sev_weight * 100
        hazard_scores[hazard] = round(score, 1)
        total_hazard += score

    # Normalize hazard score to 0-100
    max_possible = len(profile["hazards"]) * 100
    normalized_hazard = (total_hazard / max_possible) * 100 if max_possible > 0 else 0

    # Composite score: weighted combination
    composite = (
        normalized_hazard * 0.40
        + profile["population_exposure"] * 100 * 0.35
        + profile["infrastructure_vulnerability"] * 100 * 0.25
    )
    composite = round(min(100, composite), 1)

    # Determine risk level
    if composite >= 75:
        risk_level = "very_high"
    elif composite >= 60:
        risk_level = "high"
    elif composite >= 40:
        risk_level = "moderate"
    elif composite >= 20:
        risk_level = "low"
    else:
        risk_level = "very_low"

    return {
        "region": region,
        "region_name": profile["name"],
        "latitude": profile["latitude"],
        "longitude": profile["longitude"],
        "composite_score": composite,
        "risk_level": risk_level,
        "components": {
            "hazard_score": round(normalized_hazard, 1),
            "population_exposure": round(profile["population_exposure"] * 100, 1),
            "infrastructure_vulnerability": round(profile["infrastructure_vulnerability"] * 100, 1),
        },
        "hazard_breakdown": hazard_scores,
        "dominant_hazard": max(hazard_scores, key=hazard_scores.get),
    }
