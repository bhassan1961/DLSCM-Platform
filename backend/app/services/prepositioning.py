from app.services.routing import haversine


def optimize_prepositioning(warehouses: list, risk_zones: list) -> list:
    """
    Recommend optimal stock prepositioning based on warehouse proximity to risk zones.

    warehouses: list of dicts with id, name, latitude, longitude, capacity_m3, current_stock_count
    risk_zones: list of dicts with name, latitude, longitude, risk_score (0-100)

    Returns ranked list of recommendations with coverage scores and stock suggestions.
    """
    recommendations = []

    for warehouse in warehouses:
        coverage_scores = []
        covered_zones = []

        for zone in risk_zones:
            distance = haversine(
                warehouse["latitude"], warehouse["longitude"],
                zone["latitude"], zone["longitude"],
            )

            # Coverage score: inverse distance weighted by risk
            # Max effective range: 2000 km for air, diminishing for road
            if distance < 2000:
                proximity_score = max(0, (2000 - distance) / 2000) * 100
                weighted_score = proximity_score * (zone["risk_score"] / 100)
                coverage_scores.append(weighted_score)
                covered_zones.append({
                    "zone_name": zone["name"],
                    "distance_km": round(distance, 1),
                    "coverage_score": round(weighted_score, 1),
                })

        if not coverage_scores:
            continue

        avg_coverage = sum(coverage_scores) / len(coverage_scores)
        max_coverage = max(coverage_scores)

        # Stock category suggestions based on covered risk zones
        stock_suggestions = _suggest_stock(covered_zones, risk_zones)

        recommendations.append({
            "warehouse_id": warehouse["id"],
            "warehouse_name": warehouse["name"],
            "location": f"{warehouse['latitude']:.4f}, {warehouse['longitude']:.4f}",
            "capacity_m3": warehouse["capacity_m3"],
            "average_coverage_score": round(avg_coverage, 1),
            "max_coverage_score": round(max_coverage, 1),
            "zones_covered": len(covered_zones),
            "covered_zones": sorted(covered_zones, key=lambda z: z["distance_km"]),
            "stock_suggestions": stock_suggestions,
        })

    # Sort by average coverage score descending
    recommendations.sort(key=lambda r: r["average_coverage_score"], reverse=True)

    # Add rank
    for i, rec in enumerate(recommendations):
        rec["rank"] = i + 1

    return recommendations


def _suggest_stock(covered_zones: list, risk_zones: list) -> list:
    """Suggest stock categories based on the risk zones covered."""
    suggestions = []

    # Base categories always needed
    base_categories = [
        {"category": "food", "priority": "high", "reason": "Essential for all disaster responses"},
        {"category": "water", "priority": "high", "reason": "Critical WASH supplies"},
        {"category": "medical", "priority": "high", "reason": "Emergency medical kits"},
    ]
    suggestions.extend(base_categories)

    # Additional suggestions based on proximity to high-risk zones
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
