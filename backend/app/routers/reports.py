from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.disaster import Disaster
from app.models.supply_request import SupplyRequest, RequestItem
from app.models.shipment import Shipment
from app.models.coordination import ThreeWEntry
from app.models.report import DonorReport, AfterActionReview

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


# ── Schemas ────────────────────────────────────────────────────────────

class ReportGenerateRequest(BaseModel):
    disaster_id: int
    period_days: int = 30


class DonorReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    disaster_id: int
    title: str
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    content: Optional[dict] = None
    created_at: Optional[datetime] = None


class AfterActionReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    disaster_id: int
    title: str
    review_date: Optional[datetime] = None
    response_time_hours: Optional[float] = None
    cost_per_beneficiary: Optional[float] = None
    stockout_events: Optional[int] = None
    lessons_learned: Optional[str] = None
    recommendations: Optional[str] = None
    overall_score: Optional[float] = None
    created_at: Optional[datetime] = None


# ── Endpoints ──────────────────────────────────────────────────────────

@router.post("/generate", response_model=DonorReportOut)
def generate_donor_report(req: ReportGenerateRequest, db: Session = Depends(get_db)):
    disaster = db.query(Disaster).filter(Disaster.id == req.disaster_id).first()
    if not disaster:
        raise HTTPException(status_code=404, detail="Disaster not found")

    now = datetime.utcnow()
    period_start = now - timedelta(days=req.period_days)
    period_end = now

    # Aggregate data for report
    total_requests = (
        db.query(SupplyRequest)
        .filter(SupplyRequest.disaster_id == req.disaster_id)
        .count()
    )
    fulfilled_requests = (
        db.query(SupplyRequest)
        .filter(SupplyRequest.disaster_id == req.disaster_id)
        .filter(SupplyRequest.status == "delivered")
        .count()
    )
    active_shipments = (
        db.query(Shipment)
        .join(SupplyRequest)
        .filter(SupplyRequest.disaster_id == req.disaster_id)
        .filter(Shipment.status == "in_transit")
        .count()
    )
    threew_count = (
        db.query(ThreeWEntry)
        .filter(ThreeWEntry.disaster_id == req.disaster_id)
        .count()
    )
    total_beneficiaries = (
        db.query(sa_func.coalesce(sa_func.sum(ThreeWEntry.beneficiaries), 0))
        .filter(ThreeWEntry.disaster_id == req.disaster_id)
        .scalar()
    )

    content = {
        "disaster_name": disaster.name,
        "disaster_type": disaster.disaster_type,
        "severity": disaster.severity,
        "affected_population": disaster.affected_population,
        "response_summary": {
            "total_supply_requests": total_requests,
            "fulfilled_requests": fulfilled_requests,
            "active_shipments": active_shipments,
            "coordination_activities": threew_count,
            "total_beneficiaries_reached": total_beneficiaries,
        },
        "period": {
            "start": period_start.isoformat(),
            "end": period_end.isoformat(),
            "days": req.period_days,
        },
    }

    report = DonorReport(
        disaster_id=req.disaster_id,
        title=f"Donor Report - {disaster.name} - {now.strftime('%B %Y')}",
        period_start=period_start,
        period_end=period_end,
        content=content,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return DonorReportOut.model_validate(report)


@router.get("/after-action/{disaster_id}", response_model=list[AfterActionReviewOut])
def get_after_action_reviews(disaster_id: int, db: Session = Depends(get_db)):
    disaster = db.query(Disaster).filter(Disaster.id == disaster_id).first()
    if not disaster:
        raise HTTPException(status_code=404, detail="Disaster not found")

    reviews = (
        db.query(AfterActionReview)
        .filter(AfterActionReview.disaster_id == disaster_id)
        .all()
    )
    return [AfterActionReviewOut.model_validate(r) for r in reviews]
