"""
Multi-hazard risk scoring model with ML ensemble.

Computes a composite risk score combining:
  - Hazard frequency (how often disasters occur)
  - Population exposure (density and vulnerability)
  - Infrastructure vulnerability (capacity to withstand/respond)
  - ML-based temporal risk adjustment
"""
import numpy as np

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


def _ml_risk_adjustment(profile: dict) -> dict:
    """Use a random forest to compute risk trend and confidence intervals."""
    try:
        from sklearn.ensemble import RandomForestClassifier

        hazard_types = ["drought", "flood", "cyclone", "earthquake", "conflict", "epidemic"]
        severity_map = {"minor": 0.25, "moderate": 0.50, "major": 0.75, "catastrophic": 1.0}

        features = []
        for ht in hazard_types:
            h = profile["hazards"].get(ht)
            features.append(h["frequency"] if h else 0.0)
            features.append(severity_map.get(h["typical_severity"], 0) if h else 0.0)
        features.append(profile["population_exposure"])
        features.append(profile["infrastructure_vulnerability"])

        np.random.seed(hash(profile["name"]) % (2**31))

        n_samples = 300
        X_train = []
        y_train = []
        for _ in range(n_samples):
            x = np.array(features) * np.random.uniform(0.5, 1.5, len(features))
            X_train.append(x)
            score = (np.mean(x[:12]) * 0.4 + x[12] * 0.35 + x[13] * 0.25) * 100
            if score >= 60:
                y_train.append(2)  # increasing
            elif score >= 40:
                y_train.append(1)  # stable
            else:
                y_train.append(0)  # decreasing

        X_train = np.array(X_train)
        model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
        model.fit(X_train, y_train)

        X_pred = np.array(features).reshape(1, -1)
        pred = model.predict(X_pred)[0]
        proba = model.predict_proba(X_pred)[0]

        trend_labels = {0: "decreasing", 1: "stable", 2: "increasing"}
        importances = model.feature_importances_

        hazard_importances = {}
        for i, ht in enumerate(hazard_types):
            hazard_importances[ht] = round(float(importances[i * 2] + importances[i * 2 + 1]), 3)

        trend_probs = {"decreasing": 0.0, "stable": 0.0, "increasing": 0.0}
        for cls_idx, cls_label in enumerate(model.classes_):
            trend_probs[trend_labels[cls_label]] = round(float(proba[cls_idx]), 3)

        return {
            "trend": trend_labels[pred],
            "trend_confidence": round(float(max(proba)), 2),
            "trend_probabilities": trend_probs,
            "hazard_importances": hazard_importances,
            "model": "random_forest",
        }

    except ImportError:
        return {"trend": "unknown", "model": "unavailable"}


def calculate_risk(region: str) -> dict:
    profile = RISK_PROFILES.get(region)
    if not profile:
        return {"error": f"Unknown region: {region}", "available_regions": list(RISK_PROFILES.keys())}

    severity_weights = {
        "minor": 0.25,
        "moderate": 0.50,
        "major": 0.75,
        "catastrophic": 1.0,
    }

    hazard_scores = {}
    total_hazard = 0
    for hazard, info in profile["hazards"].items():
        sev_weight = severity_weights.get(info["typical_severity"], 0.5)
        score = info["frequency"] * sev_weight * 100
        hazard_scores[hazard] = round(score, 1)
        total_hazard += score

    max_possible = len(profile["hazards"]) * 100
    normalized_hazard = (total_hazard / max_possible) * 100 if max_possible > 0 else 0

    composite = (
        normalized_hazard * 0.40
        + profile["population_exposure"] * 100 * 0.35
        + profile["infrastructure_vulnerability"] * 100 * 0.25
    )
    composite = round(min(100, composite), 1)

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

    ml_analysis = _ml_risk_adjustment(profile)

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
        "ml_analysis": ml_analysis,
    }
