import math

import numpy as np

CATEGORY_RATES = {
    "food": {"rate": 0.6, "unit": "kg", "description": "Food rations"},
    "water": {"rate": 3.0, "unit": "liters", "description": "Safe drinking water"},
    "medical": {
        "rate": 0.015,
        "unit": "treatments",
        "description": "Medical treatments (15 per 1000/day)",
    },
    "shelter": {
        "rate": 0.2,
        "unit": "units",
        "description": "Shelter units (1 per family of 5)",
    },
    "hygiene": {
        "rate": 0.00667,
        "unit": "kits",
        "description": "Hygiene kits (1 per family/month)",
    },
    "nfi": {
        "rate": 0.6,
        "unit": "items",
        "description": "Non-food items (3 per family of 5)",
    },
}

SEVERITY_FACTORS = {
    "minor": 0.3,
    "moderate": 0.6,
    "major": 0.85,
    "catastrophic": 1.0,
}

DISASTER_TYPE_FEATURES = {
    "drought": [1, 0, 0, 0, 0, 0, 0.8, 0.3],
    "flood": [0, 1, 0, 0, 0, 0, 0.6, 0.7],
    "earthquake": [0, 0, 1, 0, 0, 0, 0.9, 0.5],
    "cyclone": [0, 0, 0, 1, 0, 0, 0.7, 0.8],
    "conflict": [0, 0, 0, 0, 1, 0, 0.5, 0.4],
    "epidemic": [0, 0, 0, 0, 0, 1, 0.4, 0.6],
}


def _decompose_time_series(series: np.ndarray, period: int = 7) -> dict:
    """
    STL-lite decomposition into trend, seasonal, and residual components.
    Uses convolution-based trend extraction and periodic averaging for seasonality.
    """
    n = len(series)
    if n < period * 2:
        return {"trend": series, "seasonal": np.zeros(n), "residual": np.zeros(n)}

    kernel = np.ones(period) / period
    trend = np.convolve(series, kernel, mode="same")
    trend[: period // 2] = trend[period // 2]
    trend[-(period // 2) :] = trend[-(period // 2) - 1]

    detrended = series - trend

    seasonal_pattern = np.zeros(period)
    counts = np.zeros(period)
    for i in range(n):
        seasonal_pattern[i % period] += detrended[i]
        counts[i % period] += 1
    seasonal_pattern /= np.maximum(counts, 1)
    seasonal_pattern -= np.mean(seasonal_pattern)

    seasonal = np.array([seasonal_pattern[i % period] for i in range(n)])
    residual = series - trend - seasonal

    return {
        "trend": trend,
        "seasonal": seasonal,
        "residual": residual,
        "seasonal_strength": float(
            1 - np.var(residual) / max(np.var(detrended), 1e-10)
        ),
        "trend_strength": float(
            1 - np.var(residual) / max(np.var(series - seasonal), 1e-10)
        ),
    }


def _build_ml_forecast(
    disaster_type: str,
    severity: str,
    affected_population: int,
    days_ahead: int,
    risk_context: dict | None = None,
    disruption_context: dict | None = None,
) -> dict:
    """Enhanced forecast with time-series decomposition and cross-model inputs."""
    try:
        from sklearn.ensemble import GradientBoostingRegressor

        sev_val = SEVERITY_FACTORS.get(severity, 0.6)
        type_features = DISASTER_TYPE_FEATURES.get(disaster_type, [0] * 8)

        risk_multiplier = 1.0
        if risk_context:
            composite = risk_context.get("composite_score", 50) / 100
            trend_boost = {"increasing": 0.15, "stable": 0.0, "decreasing": -0.1}
            ml = risk_context.get("ml_analysis", {})
            risk_trend = ml.get("trend", "stable")
            risk_multiplier = 0.7 + composite * 0.6 + trend_boost.get(risk_trend, 0)

        supply_risk = 0.0
        if disruption_context:
            suppliers = disruption_context.get("suppliers", [])
            if suppliers:
                high_risk = sum(
                    1 for s in suppliers if s.get("risk_level") in ("critical", "high")
                )
                supply_risk = min(1.0, high_risk / max(len(suppliers), 1))

        np.random.seed(hash((disaster_type, severity, affected_population)) % (2**31))

        n_train = 300
        X_train = []
        y_train = {cat: [] for cat in CATEGORY_RATES}

        for _ in range(n_train):
            pop = affected_population * np.random.uniform(0.3, 1.5)
            sev = sev_val * np.random.uniform(0.7, 1.3)
            day = np.random.randint(1, 91)
            day_norm = day / 90.0

            weekly_cycle = math.sin(2 * math.pi * day / 7)
            biweekly_cycle = math.sin(2 * math.pi * day / 14)
            monthly_cycle = math.sin(2 * math.pi * day / 30)

            trend = 1.0 - 0.003 * day
            if disaster_type in ("conflict", "drought"):
                trend = 1.0 + 0.002 * day

            risk_feat = np.random.uniform(0.5, 1.5)
            disruption_feat = np.random.uniform(0, 0.5)

            features = [
                pop / 1e6,
                sev,
                day_norm,
                weekly_cycle,
                biweekly_cycle,
                monthly_cycle,
                trend,
                risk_feat,
                disruption_feat,
            ] + type_features

            X_train.append(features)

            for cat, info in CATEGORY_RATES.items():
                base = info["rate"] * pop * sev
                seasonal_effect = (
                    1
                    + 0.12 * weekly_cycle
                    + 0.05 * biweekly_cycle
                    + 0.03 * monthly_cycle
                )
                supply_effect = 1 + disruption_feat * 0.2
                noise = np.random.normal(1.0, 0.08)
                y_train[cat].append(
                    base * seasonal_effect * trend * risk_feat * supply_effect * noise
                )

        X_train = np.array(X_train)
        models = {}
        for cat in CATEGORY_RATES:
            model = GradientBoostingRegressor(
                n_estimators=80, max_depth=5, learning_rate=0.1, random_state=42
            )
            model.fit(X_train, y_train[cat])
            models[cat] = model

        result = {}
        for cat, info in CATEGORY_RATES.items():
            daily_values = []

            for day in range(days_ahead):
                weekly_cycle = math.sin(2 * math.pi * day / 7)
                biweekly_cycle = math.sin(2 * math.pi * day / 14)
                monthly_cycle = math.sin(2 * math.pi * day / 30)
                trend = 1.0 - 0.003 * day
                if disaster_type in ("conflict", "drought"):
                    trend = 1.0 + 0.002 * day

                features = np.array(
                    [
                        [
                            affected_population / 1e6,
                            sev_val,
                            day / 90.0,
                            weekly_cycle,
                            biweekly_cycle,
                            monthly_cycle,
                            trend,
                            risk_multiplier,
                            supply_risk,
                        ]
                        + type_features
                    ]
                )

                pred = max(0, float(models[cat].predict(features)[0]))
                daily_values.append(pred)

            series = np.array(daily_values)
            decomp = _decompose_time_series(series, period=7)

            confidence_lower = []
            confidence_upper = []
            residual_std = float(np.std(decomp["residual"]))
            for day in range(days_ahead):
                v = daily_values[day]
                unc = max(residual_std, v * 0.05) * (1 + day * 0.003)
                confidence_lower.append(round(max(0, v - 1.96 * unc), 1))
                confidence_upper.append(round(v + 1.96 * unc, 1))

            daily_values = [round(v, 1) for v in daily_values]

            feature_names = [
                "population",
                "severity",
                "day",
                "weekly",
                "biweekly",
                "monthly",
                "trend",
                "risk",
                "supply_disruption",
            ] + [
                f"type_{t}"
                for t in [
                    "drought",
                    "flood",
                    "earthquake",
                    "cyclone",
                    "conflict",
                    "epidemic",
                    "urgency",
                    "spread",
                ]
            ]
            importances = dict(
                zip(
                    feature_names,
                    [round(float(v), 4) for v in models[cat].feature_importances_],
                )
            )

            result[cat] = {
                "total": round(sum(daily_values), 1),
                "daily": daily_values,
                "confidence_lower": confidence_lower,
                "confidence_upper": confidence_upper,
                "unit": info["unit"],
                "description": info["description"],
                "model": "gradient_boosting_enhanced",
                "decomposition": {
                    "seasonal_strength": round(decomp["seasonal_strength"], 3),
                    "trend_strength": round(decomp["trend_strength"], 3),
                    "trend_direction": "increasing"
                    if decomp["trend"][-1] > decomp["trend"][0]
                    else "decreasing",
                    "residual_std": round(residual_std, 2),
                },
                "feature_importances": importances,
                "cross_model_inputs": {
                    "risk_multiplier": round(risk_multiplier, 3),
                    "supply_disruption_risk": round(supply_risk, 3),
                },
            }

        return result

    except ImportError:
        return None


def forecast_demand(
    disaster_type: str,
    severity: str,
    affected_population: int,
    days_ahead: int = 30,
    risk_context: dict | None = None,
    disruption_context: dict | None = None,
) -> dict:
    ml_result = _build_ml_forecast(
        disaster_type,
        severity,
        affected_population,
        days_ahead,
        risk_context=risk_context,
        disruption_context=disruption_context,
    )
    if ml_result:
        return ml_result

    severity_factor = SEVERITY_FACTORS.get(severity, 0.6)
    result = {}
    for category, info in CATEGORY_RATES.items():
        base_daily = info["rate"] * affected_population * severity_factor
        daily_values = []
        for day in range(days_ahead):
            variation = 1.0 + 0.15 * math.sin(2 * math.pi * day / 7)
            daily_values.append(round(base_daily * variation, 1))
        result[category] = {
            "total": round(sum(daily_values), 1),
            "daily": daily_values,
            "unit": info["unit"],
            "description": info["description"],
            "model": "deterministic",
        }

    return result
