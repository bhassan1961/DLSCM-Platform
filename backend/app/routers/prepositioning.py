from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.inventory import Item, Stock, Warehouse
from app.models.supplier import Supplier
from app.services.disruption import predict_disruptions
from app.services.prepositioning import optimize_prepositioning
from app.services.risk_model import RISK_PROFILES, calculate_risk

router = APIRouter(prefix="/api/v1/prepositioning", tags=["prepositioning"])


@router.get("/recommendations")
def get_recommendations(db: Session = Depends(get_db)):
    warehouses = db.query(Warehouse).all()
    warehouse_data = []
    for w in warehouses:
        stock_count = db.query(Stock).filter(Stock.warehouse_id == w.id).count()
        warehouse_data.append(
            {
                "id": w.id,
                "name": w.name,
                "latitude": w.latitude,
                "longitude": w.longitude,
                "capacity_m3": w.capacity_m3,
                "current_stock_count": stock_count,
                "location": w.location,
            }
        )

    risk_zones = []
    for region_key, profile in RISK_PROFILES.items():
        risk_result = calculate_risk(region_key)
        risk_zones.append(
            {
                "name": profile["name"],
                "latitude": profile["latitude"],
                "longitude": profile["longitude"],
                "risk_score": risk_result["composite_score"],
                "risk_level": risk_result["risk_level"],
                "dominant_hazard": risk_result["dominant_hazard"],
            }
        )

    disruption_ctx = None
    suppliers = db.query(Supplier).all()
    if suppliers:
        supplier_data = [
            {
                "id": s.id,
                "name": s.name,
                "lead_time_days": s.lead_time_days or 14,
                "quality_rating": s.quality_rating or 3.0,
                "on_time_rate": 0.85,
                "capacity_utilization": 0.6,
                "defect_rate": 0.02,
                "price_volatility": 0.1,
            }
            for s in suppliers
        ]
        disruption_ctx = predict_disruptions(supplier_data)

    recommendations = optimize_prepositioning(
        warehouse_data, risk_zones, disruption_context=disruption_ctx
    )

    # Enhance with current stock details per warehouse
    for rec in recommendations:
        stocks = (
            db.query(Stock, Item)
            .join(Item, Stock.item_id == Item.id)
            .filter(Stock.warehouse_id == rec["warehouse_id"])
            .all()
        )
        stock_by_category = {}
        for stock, item in stocks:
            cat = item.category
            if cat not in stock_by_category:
                stock_by_category[cat] = {
                    "category": cat,
                    "total_quantity": 0,
                    "items": [],
                }
            stock_by_category[cat]["total_quantity"] += stock.quantity
            stock_by_category[cat]["items"].append(
                {
                    "name": item.name,
                    "sku": item.sku,
                    "quantity": stock.quantity,
                    "unit": item.unit,
                }
            )
        rec["current_stock_by_category"] = list(stock_by_category.values())

    return {
        "recommendations": recommendations,
        "risk_zones": risk_zones,
    }
