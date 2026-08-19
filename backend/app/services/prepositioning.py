import numpy as np
from app.services.routing import haversine


def optimize_prepositioning(warehouses: list, risk_zones: list, disruption_context: dict = None) -> list:
    recommendations = _stochastic_optimization(warehouses, risk_zones, disruption_context)
    if not recommendations:
        return []

    for i, rec in enumerate(recommendations):
        rec["rank"] = i + 1

    return recommendations


def _stochastic_optimization(warehouses: list, risk_zones: list, disruption_context: dict = None) -> list:
    if not warehouses or not risk_zones:
        return []

    supply_risk_factor = 1.0
    disruption_summary = None
    if disruption_context:
        suppliers = disruption_context.get("suppliers", [])
        if suppliers:
            high_risk = sum(1 for s in suppliers if s.get("risk_level") in ("critical", "high"))
            ratio = high_risk / max(len(suppliers), 1)
            supply_risk_factor = 1.0 + ratio * 0.4
            disruption_summary = {
                "total_suppliers": len(suppliers),
                "high_risk_count": high_risk,
                "supply_risk_factor": round(supply_risk_factor, 3),
            }

    n_scenarios = 200
    np.random.seed(42)

    scenarios = []
    for _ in range(n_scenarios):
        scenario = []
        for zone in risk_zones:
            base_risk = zone["risk_score"] / 100.0
            perturbed = np.clip(base_risk + np.random.normal(0, 0.15), 0, 1)
            demand_mult = 1.0 + perturbed * np.random.uniform(0.5, 3.0) * supply_risk_factor
            scenario.append({
                "name": zone["name"],
                "lat": zone["latitude"],
                "lon": zone["longitude"],
                "risk": perturbed,
                "demand_multiplier": demand_mult,
            })
        scenarios.append(scenario)

    dist_matrix = np.zeros((len(warehouses), len(risk_zones)))
    for i, wh in enumerate(warehouses):
        for j, rz in enumerate(risk_zones):
            dist_matrix[i][j] = haversine(
                wh["latitude"], wh["longitude"],
                rz["latitude"], rz["longitude"],
            )

    results = []
    for wi, wh in enumerate(warehouses):
        expected_coverage = 0.0
        worst_case = float("inf")
        best_case = 0.0
        scenario_scores = []

        for scenario in scenarios:
            score = 0.0
            for zj, sz in enumerate(scenario):
                d = dist_matrix[wi][zj]
                if d >= 2500:
                    continue
                proximity = max(0, (2500 - d) / 2500)
                transport_eff = _transport_efficiency(d)
                coverage = proximity * transport_eff * sz["risk"] * sz["demand_multiplier"]
                score += coverage

            scenario_scores.append(score)
            expected_coverage += score
            worst_case = min(worst_case, score)
            best_case = max(best_case, score)

        expected_coverage /= n_scenarios
        scores_arr = np.array(scenario_scores)
        cvar_5 = float(np.mean(scores_arr[scores_arr <= np.percentile(scores_arr, 5)])) if len(scores_arr) > 0 else 0

        covered_zones = []
        for zj, rz in enumerate(risk_zones):
            d = dist_matrix[wi][zj]
            if d < 2500:
                proximity = max(0, (2500 - d) / 2500) * 100
                weighted = proximity * (rz["risk_score"] / 100)
                covered_zones.append({
                    "zone_name": rz["name"],
                    "distance_km": round(d, 1),
                    "coverage_score": round(weighted, 1),
                })

        if not covered_zones:
            continue

        stock_suggestions = _suggest_stock(covered_zones, risk_zones)

        capacity = wh.get("capacity_m3", 1000)
        allocation = _allocate_stock(stock_suggestions, capacity, expected_coverage)

        opt_data = {
            "method": "stochastic_scenario_based",
            "n_scenarios": n_scenarios,
            "expected_value": round(expected_coverage, 3),
            "cvar_5_pct": round(cvar_5, 3),
            "worst_case": round(worst_case if worst_case != float("inf") else 0, 3),
            "best_case": round(best_case, 3),
            "robustness_score": round((cvar_5 / expected_coverage * 100) if expected_coverage > 0 else 0, 1),
            "stock_allocation": allocation,
        }
        if disruption_summary:
            opt_data["supply_chain_risk"] = disruption_summary

        results.append({
            "warehouse_id": wh["id"],
            "warehouse_name": wh["name"],
            "location": f"{wh['latitude']:.4f}, {wh['longitude']:.4f}",
            "capacity_m3": capacity,
            "average_coverage_score": round(expected_coverage * 10, 1),
            "max_coverage_score": round(best_case * 10, 1),
            "zones_covered": len(covered_zones),
            "covered_zones": sorted(covered_zones, key=lambda z: z["distance_km"]),
            "stock_suggestions": stock_suggestions,
            "optimization": opt_data,
        })

    results.sort(key=lambda r: r["average_coverage_score"], reverse=True)
    return results


def _transport_efficiency(distance_km: float) -> float:
    if distance_km < 200:
        return 1.0
    elif distance_km < 500:
        return 0.9
    elif distance_km < 1000:
        return 0.75
    elif distance_km < 2000:
        return 0.5
    else:
        return 0.25


def _allocate_stock(suggestions: list, capacity_m3: float, coverage_score: float) -> list:
    total_weight = sum(1.5 if s["priority"] == "high" else 1.0 for s in suggestions)
    allocation = []
    for s in suggestions:
        weight = 1.5 if s["priority"] == "high" else 1.0
        share = weight / total_weight
        m3 = round(capacity_m3 * share, 1)
        allocation.append({
            "category": s["category"],
            "allocated_m3": m3,
            "pct_of_capacity": round(share * 100, 1),
        })
    return allocation


def _suggest_stock(covered_zones: list, risk_zones: list) -> list:
    suggestions = [
        {"category": "food", "priority": "high", "reason": "Essential for all disaster responses"},
        {"category": "water", "priority": "high", "reason": "Critical WASH supplies"},
        {"category": "medical", "priority": "high", "reason": "Emergency medical kits"},
    ]

    close_zones = [z for z in covered_zones if z["distance_km"] < 500]
    if close_zones:
        suggestions.append({
            "category": "shelter",
            "priority": "high",
            "reason": f"Close proximity to {len(close_zones)} risk zone(s) within 500km",
        })
    else:
        suggestions.append({
            "category": "shelter",
            "priority": "medium",
            "reason": "Standard prepositioning for shelter materials",
        })

    suggestions.extend([
        {"category": "hygiene", "priority": "medium", "reason": "Hygiene kits for displaced populations"},
        {"category": "nfi", "priority": "medium", "reason": "Non-food items for household needs"},
    ])

    return suggestions
