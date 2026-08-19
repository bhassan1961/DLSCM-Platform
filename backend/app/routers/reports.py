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
    template: str = "generic"


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


class AfterActionReviewCreate(BaseModel):
    disaster_id: int
    title: str
    review_date: datetime
    response_time_hours: Optional[float] = None
    cost_per_beneficiary: Optional[float] = None
    stockout_events: Optional[int] = None
    lessons_learned: Optional[str] = None
    recommendations: Optional[str] = None
    overall_score: Optional[float] = None


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

    # Template-specific content sections
    if req.template == "echo":
        content["template"] = "ECHO"
        content["template_title"] = "ECHO Single Form Report"
        content["sections"] = {
            "action_description": f"Emergency response to {disaster.name} ({disaster.disaster_type}). Affected population: {disaster.affected_population:,}.",
            "results_achieved": f"Supply requests processed: {total_requests}. Fulfilled: {fulfilled_requests}. Beneficiaries reached: {total_beneficiaries:,} through {threew_count} coordination activities.",
            "means_and_costs": f"Active shipments: {active_shipments}. Operational period: {req.period_days} days.",
            "coordination": f"{threew_count} inter-agency coordination activities recorded.",
            "visibility": "ECHO logo displayed at all distribution points. Partner acknowledgment in all public communications.",
        }
    elif req.template == "usaid":
        content["template"] = "USAID"
        content["template_title"] = "USAID Performance Report"
        content["sections"] = {
            "executive_summary": f"USAID-funded response to {disaster.name}. {fulfilled_requests} of {total_requests} supply requests fulfilled during the {req.period_days}-day reporting period.",
            "program_description": f"Disaster type: {disaster.disaster_type}. Severity: {disaster.severity}. Affected population: {disaster.affected_population:,}.",
            "indicator_tracking": {
                "IR1_supplies_delivered": fulfilled_requests,
                "IR2_beneficiaries_reached": total_beneficiaries,
                "IR3_coordination_activities": threew_count,
                "IR4_active_shipments": active_shipments,
            },
            "challenges_and_lessons": "Refer to after-action review for detailed lessons learned.",
            "financial_summary": "Detailed financial breakdown available upon request.",
        }
    elif req.template == "fcdo":
        content["template"] = "FCDO"
        content["template_title"] = "FCDO Annual Review"
        content["sections"] = {
            "summary_and_context": f"Response to {disaster.name} ({disaster.disaster_type}, {disaster.severity} severity) affecting {disaster.affected_population:,} people.",
            "output_delivery": f"Total supply requests: {total_requests}. Fulfillment rate: {round(fulfilled_requests/max(total_requests,1)*100)}%. Active logistics operations: {active_shipments} shipments.",
            "outcome_assessment": f"Reached {total_beneficiaries:,} beneficiaries through {threew_count} coordination activities across partner organizations.",
            "vfm_assessment": "Value for Money assessment: Good. Cost efficiency metrics available in after-action review.",
            "risk_assessment": f"Current severity level: {disaster.severity}. Ongoing monitoring through DLSCM risk dashboard.",
        }
    else:
        content["template"] = "Generic"
        content["template_title"] = "Standard Donor Report"

    report = DonorReport(
        disaster_id=req.disaster_id,
        title=f"{content.get('template_title', 'Donor Report')} - {disaster.name} - {now.strftime('%B %Y')}",
        period_start=period_start,
        period_end=period_end,
        content=content,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return DonorReportOut.model_validate(report)



@router.get("", response_model=list[DonorReportOut])
def list_reports(db: Session = Depends(get_db)):
    reports = db.query(DonorReport).order_by(DonorReport.created_at.desc()).all()
    return [DonorReportOut.model_validate(r) for r in reports]


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


@router.post("/after-action", response_model=AfterActionReviewOut, status_code=201)
def create_after_action_review(review: AfterActionReviewCreate, db: Session = Depends(get_db)):
    disaster = db.query(Disaster).filter(Disaster.id == review.disaster_id).first()
    if not disaster:
        raise HTTPException(status_code=404, detail="Disaster not found")
    r = AfterActionReview(**review.model_dump())
    db.add(r)
    db.commit()
    db.refresh(r)
    return AfterActionReviewOut.model_validate(r)
