"""
Crisis Intelligence API

Provides aggregated intelligence feeds per disaster from:
- ReliefWeb (UN OCHA situation reports & analyses)
- GDACS (real-time disaster alerts)
- Humanitarian news RSS feeds
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.disaster import Disaster
from app.services.intelligence import get_crisis_intelligence, fetch_gdacs_live_alerts, fetch_live_news, ALL_NEWS_FEEDS

router = APIRouter(prefix="/api/v1/intelligence", tags=["Intelligence"])


@router.get("/live-alerts")
async def get_live_alerts():
    """Fetch all active GDACS disaster alerts globally with coordinates."""
    alerts = await fetch_gdacs_live_alerts()
    return {"alerts": alerts, "total": len(alerts), "source": "GDACS"}


@router.get("/news-feeds")
async def list_available_feeds():
    """List all available news feed sources."""
    return {"feeds": ALL_NEWS_FEEDS}


@router.get("/news")
async def get_live_news(
    feeds: Optional[str] = Query(None, description="Comma-separated feed IDs to fetch"),
    limit: int = Query(20, ge=1, le=50),
):
    """Fetch latest news from RSS feeds. Pass ?feeds=reliefweb,icrc to select sources."""
    feed_ids = feeds.split(",") if feeds else None
    result = await fetch_live_news(feed_ids=feed_ids, max_per_feed=limit)
    return result


@router.get("")
async def list_intelligence_summary(
    db: Session = Depends(get_db),
    status: Optional[str] = Query("active"),
):
    """Get a summary of available intelligence for all active disasters."""
    query = db.query(Disaster)
    if status:
        query = query.filter(Disaster.status == status)
    disasters = query.all()

    summaries = []
    for d in disasters:
        summaries.append({
            "disaster_id": d.id,
            "disaster_name": d.name,
            "country": d.country,
            "disaster_type": d.disaster_type,
            "severity": d.severity,
            "status": d.status,
            "affected_population": d.affected_population,
            "coordinates": {"lat": d.latitude, "lng": d.longitude},
        })

    return {"disasters": summaries, "total": len(summaries)}


@router.get("/{disaster_id}")
async def get_intelligence(
    disaster_id: int,
    days_back: int = Query(90, ge=1, le=365),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    disaster = db.query(Disaster).filter(Disaster.id == disaster_id).first()
    if not disaster:
        raise HTTPException(status_code=404, detail="Disaster not found")

    result = await get_crisis_intelligence(
        disaster_name=disaster.name,
        country=disaster.country,
        disaster_type=disaster.disaster_type,
        region=disaster.region,
        days_back=days_back,
        limit=limit,
    )

    result["disaster_id"] = disaster.id
    result["disaster_status"] = disaster.status
    result["affected_population"] = disaster.affected_population
    result["coordinates"] = {"lat": disaster.latitude, "lng": disaster.longitude}

    return result
