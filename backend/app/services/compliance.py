from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.inventory import Stock, Item
from app.models.supply_request import SupplyRequest
from app.models.shipment import Shipment
from app.models.disaster import Disaster


def check_compliance(db: Session) -> dict:
    """
    Run compliance checks against Sphere humanitarian standards,
    inventory health, and operational metrics.
    """

    # ── Sphere Standards ──────────────────────────────────────────────
    sphere_standards = []

    # Compute total affected population across active disasters
    active_disasters = db.query(Disaster).filter(Disaster.status == "active").all()
    total_affected = sum(d.affected_population for d in active_disasters) if active_disasters else 1

    # Water: at least 15L/person/day
    water_stocks = (
        db.query(Stock)
        .join(Item)
        .filter(Item.category == "water")
        .all()
    )
    water_total = sum(s.quantity for s in water_stocks)
    water_per_person = round(water_total / max(total_affected, 1), 2)
    sphere_standards.append({
        "standard": "water",
        "description": "Minimum 15L of water per person per day",
        "status": "met" if water_per_person >= 15 else ("at_risk" if water_per_person >= 10 else "not_met"),
        "current_value": water_per_person,
        "target_value": 15.0,
    })

    # Shelter: at least 3.5m2/person
    shelter_stocks = (
        db.query(Stock)
        .join(Item)
        .filter(Item.category == "shelter")
        .all()
    )
    shelter_total = sum(s.quantity for s in shelter_stocks)
    shelter_per_person = round(shelter_total / max(total_affected, 1), 4)
    sphere_standards.append({
        "standard": "shelter",
        "description": "Minimum 3.5 m2 covered living space per person",
        "status": "met" if shelter_per_person >= 3.5 else ("at_risk" if shelter_per_person >= 2.0 else "not_met"),
        "current_value": shelter_per_person,
        "target_value": 3.5,
    })

    # Nutrition: at least 2100 kcal/person/day
    food_stocks = (
        db.query(Stock)
        .join(Item)
        .filter(Item.category == "food")
        .all()
    )
    food_total = sum(s.quantity for s in food_stocks)
    food_per_person = round(food_total / max(total_affected, 1), 2)
    sphere_standards.append({
        "standard": "nutrition",
        "description": "Minimum 2100 kcal per person per day",
        "status": "met" if food_per_person >= 2100 else ("at_risk" if food_per_person >= 1500 else "not_met"),
        "current_value": food_per_person,
        "target_value": 2100.0,
    })

    # ── Inventory Health ──────────────────────────────────────────────
    now = datetime.utcnow()
    all_stocks = db.query(Stock).all()
    total_items = len(all_stocks)

    items_expiring_30 = sum(
        1 for s in all_stocks
        if s.expiry_date and s.expiry_date <= now + timedelta(days=30)
    )
    items_expiring_90 = sum(
        1 for s in all_stocks
        if s.expiry_date and s.expiry_date <= now + timedelta(days=90)
    )
    stockout_risk = sum(1 for s in all_stocks if s.quantity < 100)

    inventory_health = {
        "total_items": total_items,
        "items_expiring_30_days": items_expiring_30,
        "items_expiring_90_days": items_expiring_90,
        "stockout_risk_count": stockout_risk,
    }

    # ── Operational Metrics ───────────────────────────────────────────
    all_requests = db.query(SupplyRequest).all()
    all_shipments = db.query(Shipment).all()

    # Average fulfillment time (for delivered requests)
    fulfillment_days_list = []
    for sr in all_requests:
        if sr.status == "delivered" and sr.created_at and sr.updated_at:
            delta = (sr.updated_at - sr.created_at).total_seconds() / 86400
            fulfillment_days_list.append(delta)
    avg_fulfillment = round(sum(fulfillment_days_list) / len(fulfillment_days_list), 1) if fulfillment_days_list else 0.0

    # Overdue requests: pending or approved for more than 7 days
    overdue_count = sum(
        1 for sr in all_requests
        if sr.status in ("pending", "approved")
        and sr.created_at
        and (now - sr.created_at).days > 7
    )

    # Delivery success rate
    total_shipments = len(all_shipments)
    delivered_shipments = sum(1 for s in all_shipments if s.status == "delivered")
    delivery_rate = round(delivered_shipments / max(total_shipments, 1) * 100, 1)

    operational_metrics = {
        "avg_request_fulfillment_days": avg_fulfillment,
        "requests_overdue": overdue_count,
        "delivery_success_rate": delivery_rate,
    }

    # ── Overall Score ─────────────────────────────────────────────────
    # Score: weighted average of sphere compliance, inventory health, and ops metrics
    sphere_score = sum(30 if c["status"] == "met" else (15 if c["status"] == "at_risk" else 0) for c in sphere_standards)
    sphere_max = 30 * len(sphere_standards)
    sphere_pct = (sphere_score / sphere_max * 100) if sphere_max > 0 else 0

    inv_score = 100
    if total_items > 0:
        inv_score -= (items_expiring_30 / total_items) * 30
        inv_score -= (stockout_risk / total_items) * 20

    ops_score = min(delivery_rate, 100)

    overall_score = round(sphere_pct * 0.4 + inv_score * 0.3 + ops_score * 0.3, 1)

    return {
        "sphere_standards": sphere_standards,
        "inventory_health": inventory_health,
        "operational_metrics": operational_metrics,
        "overall_score": overall_score,
    }
