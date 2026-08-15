import random
import math


# Sector weight profiles by disaster type (sum to ~1.0 each)
DISASTER_SECTOR_WEIGHTS = {
    "earthquake": {
        "infrastructure": 0.35,
        "housing": 0.30,
        "health": 0.15,
        "education": 0.10,
        "agriculture": 0.10,
    },
    "flood": {
        "infrastructure": 0.20,
        "housing": 0.25,
        "health": 0.10,
        "education": 0.10,
        "agriculture": 0.35,
    },
    "cyclone": {
        "infrastructure": 0.30,
        "housing": 0.30,
        "health": 0.10,
        "education": 0.10,
        "agriculture": 0.20,
    },
    "drought": {
        "infrastructure": 0.05,
        "housing": 0.05,
        "health": 0.25,
        "education": 0.15,
        "agriculture": 0.50,
    },
    "conflict": {
        "infrastructure": 0.30,
        "housing": 0.25,
        "health": 0.25,
        "education": 0.15,
        "agriculture": 0.05,
    },
    "epidemic": {
        "infrastructure": 0.05,
        "housing": 0.05,
        "health": 0.60,
        "education": 0.20,
        "agriculture": 0.10,
    },
}

SEVERITY_BASE_SCORES = {
    "minor": 25,
    "moderate": 50,
    "major": 72,
    "catastrophic": 90,
}


def assess_damage(disaster_type: str, severity: str) -> dict:
    """
    Generate synthetic damage assessment scores for a disaster.

    Returns sector scores (0-100) and an overall damage index,
    weighted according to the disaster type.
    """
    weights = DISASTER_SECTOR_WEIGHTS.get(disaster_type, DISASTER_SECTOR_WEIGHTS["flood"])
    base_score = SEVERITY_BASE_SCORES.get(severity, 50)

    # Use a deterministic seed based on disaster_type + severity
    seed_val = hash(f"{disaster_type}-{severity}") % 10000
    rng = random.Random(seed_val)

    sector_scores = {}
    for sector, weight in weights.items():
        # Higher weight means more damage for this disaster type
        sector_base = base_score * (0.5 + weight)
        # Add controlled variation
        variation = rng.uniform(-10, 10)
        score = max(0, min(100, sector_base + variation))
        sector_scores[sector] = round(score, 1)

    # Overall index is weighted average
    overall = sum(
        sector_scores[s] * weights[s] for s in sector_scores
    )
    overall_index = round(overall, 1)

    # Categorize overall damage
    if overall_index >= 75:
        damage_category = "severe"
    elif overall_index >= 50:
        damage_category = "substantial"
    elif overall_index >= 25:
        damage_category = "moderate"
    else:
        damage_category = "light"

    return {
        "disaster_type": disaster_type,
        "severity": severity,
        "sector_scores": sector_scores,
        "overall_damage_index": overall_index,
        "damage_category": damage_category,
        "assessment_notes": _generate_notes(disaster_type, sector_scores, damage_category),
    }


def _generate_notes(disaster_type: str, sector_scores: dict, damage_category: str) -> list:
    """Generate human-readable assessment notes based on scores."""
    notes = []

    highest_sector = max(sector_scores, key=sector_scores.get)
    lowest_sector = min(sector_scores, key=sector_scores.get)

    notes.append(f"Most affected sector: {highest_sector} (score: {sector_scores[highest_sector]})")
    notes.append(f"Least affected sector: {lowest_sector} (score: {sector_scores[lowest_sector]})")

    if sector_scores.get("health", 0) > 70:
        notes.append("URGENT: Health infrastructure critically compromised. Immediate medical surge required.")

    if sector_scores.get("infrastructure", 0) > 60:
        notes.append("WARNING: Significant infrastructure damage may impede logistics operations.")

    if sector_scores.get("agriculture", 0) > 60:
        notes.append("Food security at risk due to agricultural damage. Long-term food assistance likely needed.")

    return notes
