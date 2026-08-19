"""
Multi-stream anomaly detection for inventory and shipment data.

Uses Isolation Forest for multivariate anomaly detection and
EWMA (Exponentially Weighted Moving Average) for change-point detection.
"""

import numpy as np


def detect_inventory_anomalies(stock_records: list) -> dict:
    """
    Detect anomalous inventory patterns across warehouses.

    Each record: {warehouse_id, warehouse_name, item_id, item_name, category,
                  quantity, min_required, last_updated_ts}
    """
    if len(stock_records) < 5:
        return {"anomalies": [], "summary": {"method": "insufficient_data"}}

    try:
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler

        features = []
        for r in stock_records:
            qty = r.get("quantity", 0)
            min_req = r.get("min_required", 1)
            stock_ratio = qty / max(min_req, 1)
            overstock = max(0, qty - min_req * 3) / max(min_req, 1)
            understock = max(0, min_req - qty) / max(min_req, 1)
            days_since_update = r.get("days_since_update", 0)

            features.append(
                [
                    stock_ratio,
                    overstock,
                    understock,
                    days_since_update,
                    qty,
                ]
            )

        X = np.array(features)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        iso = IsolationForest(
            n_estimators=100,
            contamination=0.1,
            random_state=42,
        )
        iso.fit(X_scaled)

        scores = iso.decision_function(X_scaled)
        predictions = iso.predict(X_scaled)

        anomalies = []
        for i, r in enumerate(stock_records):
            if predictions[i] == -1:
                severity = _anomaly_severity(float(scores[i]))
                reason = _diagnose_inventory(r, features[i])
                anomalies.append(
                    {
                        "warehouse_id": r.get("warehouse_id"),
                        "warehouse_name": r.get("warehouse_name"),
                        "item_id": r.get("item_id"),
                        "item_name": r.get("item_name"),
                        "category": r.get("category"),
                        "anomaly_score": round(float(-scores[i]), 3),
                        "severity": severity,
                        "reason": reason,
                        "current_quantity": r.get("quantity"),
                        "min_required": r.get("min_required"),
                    }
                )

        anomalies.sort(key=lambda a: a["anomaly_score"], reverse=True)

        return {
            "anomalies": anomalies,
            "summary": {
                "method": "isolation_forest",
                "total_records": len(stock_records),
                "anomalies_found": len(anomalies),
                "anomaly_rate": round(len(anomalies) / len(stock_records), 3),
            },
        }

    except ImportError:
        return _fallback_inventory_anomalies(stock_records)


def detect_shipment_anomalies(shipments: list) -> dict:
    """
    Detect anomalous shipment patterns.

    Each record: {id, tracking_id, status, origin, destination,
                  estimated_days, actual_days, delay_days, items_count}
    """
    if len(shipments) < 5:
        return {"anomalies": [], "summary": {"method": "insufficient_data"}}

    try:
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler

        features = []
        for s in shipments:
            est = s.get("estimated_days", 7)
            actual = s.get("actual_days", est)
            delay = s.get("delay_days", max(0, actual - est))
            delay_ratio = delay / max(est, 1)
            items = s.get("items_count", 1)

            features.append(
                [
                    est,
                    actual,
                    delay,
                    delay_ratio,
                    items,
                ]
            )

        X = np.array(features)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        iso = IsolationForest(
            n_estimators=100,
            contamination=0.12,
            random_state=42,
        )
        iso.fit(X_scaled)

        scores = iso.decision_function(X_scaled)
        predictions = iso.predict(X_scaled)

        anomalies = []
        for i, s in enumerate(shipments):
            if predictions[i] == -1:
                severity = _anomaly_severity(float(scores[i]))
                reason = _diagnose_shipment(s, features[i])
                anomalies.append(
                    {
                        "shipment_id": s.get("id"),
                        "tracking_id": s.get("tracking_id"),
                        "anomaly_score": round(float(-scores[i]), 3),
                        "severity": severity,
                        "reason": reason,
                        "status": s.get("status"),
                        "delay_days": s.get("delay_days", 0),
                        "origin": s.get("origin"),
                        "destination": s.get("destination"),
                    }
                )

        anomalies.sort(key=lambda a: a["anomaly_score"], reverse=True)

        return {
            "anomalies": anomalies,
            "summary": {
                "method": "isolation_forest",
                "total_shipments": len(shipments),
                "anomalies_found": len(anomalies),
                "anomaly_rate": round(len(anomalies) / len(shipments), 3),
            },
        }

    except ImportError:
        return _fallback_shipment_anomalies(shipments)


def detect_consumption_drift(daily_consumption: list[float], window: int = 7) -> dict:
    """
    EWMA-based change-point detection on daily consumption rates.
    Returns drift alerts when consumption deviates significantly from trend.
    """
    if len(daily_consumption) < window * 2:
        return {"drift_detected": False, "reason": "insufficient_data"}

    series = np.array(daily_consumption, dtype=float)
    alpha = 2.0 / (window + 1)
    ewma = np.zeros_like(series)
    ewma[0] = series[0]
    for i in range(1, len(series)):
        ewma[i] = alpha * series[i] + (1 - alpha) * ewma[i - 1]

    ewma_var = np.zeros_like(series)
    ewma_var[0] = 0
    for i in range(1, len(series)):
        ewma_var[i] = alpha * (series[i] - ewma[i]) ** 2 + (1 - alpha) * ewma_var[i - 1]

    ewma_std = np.sqrt(ewma_var)

    recent = series[-window:]
    recent_mean = float(np.mean(recent))
    baseline_mean = float(np.mean(ewma[:-window]))
    baseline_std = (
        float(np.mean(ewma_std[:-window])) if np.mean(ewma_std[:-window]) > 0 else 1.0
    )

    z_score = (recent_mean - baseline_mean) / max(baseline_std, 0.01)
    drift_detected = abs(z_score) > 2.0

    if drift_detected:
        direction = "increasing" if z_score > 0 else "decreasing"
        magnitude = "significant" if abs(z_score) > 3.0 else "moderate"
    else:
        direction = "stable"
        magnitude = "none"

    return {
        "drift_detected": drift_detected,
        "z_score": round(z_score, 3),
        "direction": direction,
        "magnitude": magnitude,
        "recent_mean": round(recent_mean, 2),
        "baseline_mean": round(baseline_mean, 2),
        "ewma_current": round(float(ewma[-1]), 2),
        "method": "ewma_change_point",
    }


def _anomaly_severity(score: float) -> str:
    if score < -0.3:
        return "critical"
    elif score < -0.15:
        return "high"
    elif score < -0.05:
        return "moderate"
    return "low"


def _diagnose_inventory(record: dict, features: list) -> str:
    stock_ratio, overstock, understock, days_stale, qty = features
    reasons = []
    if understock > 0.5:
        reasons.append(
            f"critically understocked ({record.get('quantity')}/{record.get('min_required')})"
        )
    if overstock > 2.0:
        reasons.append(f"excessive overstock ({stock_ratio:.1f}x minimum)")
    if days_stale > 30:
        reasons.append(f"stale record ({int(days_stale)} days since update)")
    if qty == 0:
        reasons.append("zero stock on hand")
    return "; ".join(reasons) if reasons else "unusual stock pattern"


def _diagnose_shipment(record: dict, features: list) -> str:
    _est, _actual, delay, delay_ratio, items = features
    reasons = []
    if delay > 7:
        reasons.append(f"severely delayed ({int(delay)} days over estimate)")
    elif delay > 3:
        reasons.append(f"delayed ({int(delay)} days over estimate)")
    if delay_ratio > 1.0:
        reasons.append(f"delay exceeds original estimate by {delay_ratio:.0%}")
    if items > 50:
        reasons.append(f"unusually large shipment ({int(items)} items)")
    return "; ".join(reasons) if reasons else "unusual shipment pattern"


def _fallback_inventory_anomalies(records: list) -> dict:
    anomalies = []
    for r in records:
        qty = r.get("quantity", 0)
        min_req = r.get("min_required", 1)
        if qty < min_req * 0.3 or qty > min_req * 5:
            anomalies.append(
                {
                    "warehouse_name": r.get("warehouse_name"),
                    "item_name": r.get("item_name"),
                    "severity": "high" if qty < min_req * 0.3 else "moderate",
                    "reason": "critically low"
                    if qty < min_req * 0.3
                    else "excessive overstock",
                    "current_quantity": qty,
                    "min_required": min_req,
                }
            )
    return {"anomalies": anomalies, "summary": {"method": "heuristic_fallback"}}


def _fallback_shipment_anomalies(shipments: list) -> dict:
    anomalies = []
    for s in shipments:
        delay = s.get("delay_days", 0)
        if delay > 5:
            anomalies.append(
                {
                    "tracking_id": s.get("tracking_id"),
                    "severity": "critical" if delay > 10 else "high",
                    "reason": f"delayed {delay} days",
                    "delay_days": delay,
                }
            )
    return {"anomalies": anomalies, "summary": {"method": "heuristic_fallback"}}
