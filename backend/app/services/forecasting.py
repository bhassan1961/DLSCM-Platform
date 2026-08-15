import math
from typing import Optional


# Category rates per person per day
CATEGORY_RATES = {
    "food": {"rate": 0.6, "unit": "kg", "description": "Food rations"},
    "water": {"rate": 3.0, "unit": "liters", "description": "Safe drinking water"},
    "medical": {"rate": 0.015, "unit": "treatments", "description": "Medical treatments (15 per 1000/day)"},
    "shelter": {"rate": 0.2, "unit": "units", "description": "Shelter units (1 per family of 5)"},
    "hygiene": {"rate": 0.00667, "unit": "kits", "description": "Hygiene kits (1 per family/month)"},
    "nfi": {"rate": 0.6, "unit": "items", "description": "Non-food items (3 per family of 5)"},
}

SEVERITY_FACTORS = {
    "minor": 0.3,
    "moderate": 0.6,
    "major": 0.85,
    "catastrophic": 1.0,
}


def forecast_demand(
    disaster_type: str,
    severity: str,
    affected_population: int,
    days_ahead: int = 30,
) -> dict:
    """
    Generate deterministic demand forecasts by category.

    Returns a dict keyed by category with:
      - total: total quantity over the forecast period
      - daily: list of daily demand values (with sine variation)
      - unit: unit of measure
    """
    severity_factor = SEVERITY_FACTORS.get(severity, 0.6)
    result = {}

    for category, info in CATEGORY_RATES.items():
        base_daily = info["rate"] * affected_population * severity_factor

        daily_values = []
        for day in range(days_ahead):
            # Sine wave variation: +/- 15% amplitude, 7-day cycle
            variation = 1.0 + 0.15 * math.sin(2 * math.pi * day / 7)
            daily_values.append(round(base_daily * variation, 1))

        total = round(sum(daily_values), 1)

        result[category] = {
            "total": total,
            "daily": daily_values,
            "unit": info["unit"],
            "description": info["description"],
        }

    return result
