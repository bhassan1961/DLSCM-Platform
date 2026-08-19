"""
Supply disruption prediction using Isolation Forest anomaly detection
and ensemble methods for supply chain risk scoring.
"""
import numpy as np


def _build_disruption_model(supplier_data: list) -> dict:
    """Train an Isolation Forest to detect anomalous supplier behavior."""
    try:
        from sklearn.ensemble import IsolationForest, GradientBoostingClassifier
        from sklearn.preprocessing import StandardScaler

        if len(supplier_data) < 3:
            return {"error": "Need at least 3 suppliers for disruption analysis"}

        features = []
        for s in supplier_data:
            features.append([
                s.get("lead_time_days", 14),
                s.get("quality_rating", 3.0),
                s.get("on_time_rate", 0.8),
                s.get("capacity_utilization", 0.6),
                s.get("defect_rate", 0.02),
                s.get("price_volatility", 0.1),
            ])

        X = np.array(features)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        iso_forest = IsolationForest(
            n_estimators=100,
            contamination=0.15,
            random_state=42,
        )
        iso_forest.fit(X_scaled)

        anomaly_scores = iso_forest.decision_function(X_scaled)
        predictions = iso_forest.predict(X_scaled)

        np.random.seed(42)
        n_synthetic = 300
        X_synth = np.random.randn(n_synthetic, X_scaled.shape[1])
        y_synth = (iso_forest.predict(X_synth) == -1).astype(int)

        gb_model = GradientBoostingClassifier(
            n_estimators=50, max_depth=3, random_state=42,
        )
        gb_model.fit(X_synth, y_synth)

        feature_names = [
            "lead_time", "quality_rating", "on_time_rate",
            "capacity_utilization", "defect_rate", "price_volatility",
        ]
        importances = dict(zip(feature_names, [round(float(v), 3) for v in gb_model.feature_importances_]))

        results = []
        for i, s in enumerate(supplier_data):
            raw_score = float(anomaly_scores[i])
            risk_score = round(max(0, min(100, (1 - (raw_score + 0.5)) * 100)), 1)

            gb_proba = gb_model.predict_proba(X_scaled[i:i+1])[0]
            ensemble_risk = round((risk_score * 0.6 + float(gb_proba[1] if len(gb_proba) > 1 else gb_proba[0]) * 100 * 0.4), 1)

            if ensemble_risk >= 70:
                level = "critical"
            elif ensemble_risk >= 50:
                level = "high"
            elif ensemble_risk >= 30:
                level = "moderate"
            else:
                level = "low"

            results.append({
                "supplier_id": s.get("id"),
                "supplier_name": s.get("name", f"Supplier {i+1}"),
                "disruption_risk_score": ensemble_risk,
                "risk_level": level,
                "is_anomaly": bool(predictions[i] == -1),
                "anomaly_score": round(raw_score, 4),
                "contributing_factors": _identify_factors(X[i], feature_names),
            })

        results.sort(key=lambda r: r["disruption_risk_score"], reverse=True)

        return {
            "suppliers": results,
            "model_info": {
                "algorithm": "ensemble (isolation_forest + gradient_boosting)",
                "feature_importances": importances,
                "n_anomalies": int(sum(1 for p in predictions if p == -1)),
                "n_total": len(supplier_data),
            },
        }

    except ImportError:
        return _fallback_disruption(supplier_data)


def _identify_factors(feature_values, feature_names):
    """Identify which factors contribute most to disruption risk."""
    thresholds = {
        "lead_time": (21, "high", "Lead time exceeds 21 days"),
        "quality_rating": (2.5, "low", "Quality rating below 2.5"),
        "on_time_rate": (0.7, "low", "On-time delivery rate below 70%"),
        "capacity_utilization": (0.9, "high", "Capacity utilization above 90%"),
        "defect_rate": (0.05, "high", "Defect rate exceeds 5%"),
        "price_volatility": (0.2, "high", "Price volatility above 20%"),
    }
    factors = []
    for val, name in zip(feature_values, feature_names):
        if name in thresholds:
            thresh, direction, desc = thresholds[name]
            if (direction == "high" and val > thresh) or (direction == "low" and val < thresh):
                factors.append({"factor": name, "value": round(float(val), 3), "description": desc})
    return factors


def _fallback_disruption(supplier_data: list) -> dict:
    """Simple heuristic fallback when scikit-learn unavailable."""
    results = []
    for s in supplier_data:
        score = 0
        if s.get("lead_time_days", 14) > 21:
            score += 25
        if s.get("quality_rating", 3) < 3:
            score += 20
        if s.get("on_time_rate", 0.8) < 0.75:
            score += 30
        if s.get("defect_rate", 0.02) > 0.05:
            score += 25

        level = "critical" if score >= 70 else "high" if score >= 50 else "moderate" if score >= 30 else "low"
        results.append({
            "supplier_id": s.get("id"),
            "supplier_name": s.get("name"),
            "disruption_risk_score": score,
            "risk_level": level,
            "is_anomaly": score >= 60,
        })

    return {"suppliers": results, "model_info": {"algorithm": "heuristic_fallback"}}


def predict_disruptions(supplier_data: list) -> dict:
    return _build_disruption_model(supplier_data)
