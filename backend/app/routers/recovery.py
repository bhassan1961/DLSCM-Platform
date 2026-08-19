from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.disaster import Disaster
from app.models.recovery import RecoveryPlan, RecoveryProcurement

router = APIRouter(prefix="/api/v1/recovery", tags=["recovery"])


class RecoveryPlanCreate(BaseModel):
    disaster_id: int
    title: str
    description: str | None = None
    target_completion: str | None = None


class PhaseUpdate(BaseModel):
    phase: str
    status: str
    notes: str | None = None


class ProcurementCreate(BaseModel):
    item: str
    category: str
    quantity: int
    unit_cost: float
    supplier: str | None = None
    status: str = "planned"


LIFECYCLE_PHASES = [
    {"phase": "assessment", "label": "Damage Assessment", "order": 1},
    {"phase": "stabilization", "label": "Immediate Stabilization", "order": 2},
    {"phase": "short_term", "label": "Short-Term Recovery", "order": 3},
    {"phase": "long_term", "label": "Long-Term Reconstruction", "order": 4},
    {"phase": "resilience", "label": "Resilience Building", "order": 5},
]


def _plan_to_dict(plan: RecoveryPlan) -> dict:
    return {
        "id": plan.id,
        "disaster_id": plan.disaster_id,
        "disaster_name": plan.disaster.name if plan.disaster else None,
        "title": plan.title,
        "description": plan.description,
        "target_completion": plan.target_completion,
        "current_phase": plan.current_phase,
        "phases": plan.phases,
        "procurement": [
            {
                "id": p.id,
                "item": p.item,
                "category": p.category,
                "quantity": p.quantity,
                "unit_cost": p.unit_cost,
                "total_cost": p.total_cost,
                "supplier": p.supplier,
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in plan.procurement_items
        ],
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
    }


@router.get("/plans")
def list_plans(disaster_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(RecoveryPlan)
    if disaster_id:
        query = query.filter(RecoveryPlan.disaster_id == disaster_id)
    return [_plan_to_dict(p) for p in query.all()]


@router.post("/plans")
def create_plan(req: RecoveryPlanCreate, db: Session = Depends(get_db)):
    disaster = db.query(Disaster).filter(Disaster.id == req.disaster_id).first()
    if not disaster:
        raise HTTPException(status_code=404, detail="Disaster not found")

    phases = {
        p["phase"]: {"status": "pending", "notes": None} for p in LIFECYCLE_PHASES
    }
    phases["assessment"]["status"] = "in_progress"

    plan = RecoveryPlan(
        disaster_id=req.disaster_id,
        title=req.title,
        description=req.description,
        target_completion=req.target_completion,
        current_phase="assessment",
        phases=phases,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return _plan_to_dict(plan)


@router.patch("/plans/{plan_id}/phase")
def update_phase(plan_id: int, req: PhaseUpdate, db: Session = Depends(get_db)):
    plan = db.query(RecoveryPlan).filter(RecoveryPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Recovery plan not found")

    phases = dict(plan.phases)
    if req.phase not in phases:
        raise HTTPException(status_code=400, detail=f"Invalid phase: {req.phase}")

    phases[req.phase]["status"] = req.status
    phases[req.phase]["notes"] = req.notes

    if req.status == "completed":
        phase_order = {p["phase"]: p["order"] for p in LIFECYCLE_PHASES}
        current_order = phase_order.get(req.phase, 0)
        for p in LIFECYCLE_PHASES:
            if p["order"] == current_order + 1:
                plan.current_phase = p["phase"]
                if phases[p["phase"]]["status"] == "pending":
                    phases[p["phase"]]["status"] = "in_progress"
                break

    plan.phases = phases
    db.commit()
    db.refresh(plan)
    return _plan_to_dict(plan)


@router.get("/plans/{plan_id}/procurement")
def list_procurement(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(RecoveryPlan).filter(RecoveryPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Recovery plan not found")
    return [
        {
            "id": p.id,
            "item": p.item,
            "category": p.category,
            "quantity": p.quantity,
            "unit_cost": p.unit_cost,
            "total_cost": p.total_cost,
            "supplier": p.supplier,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in plan.procurement_items
    ]


@router.post("/plans/{plan_id}/procurement")
def add_procurement(
    plan_id: int, req: ProcurementCreate, db: Session = Depends(get_db)
):
    plan = db.query(RecoveryPlan).filter(RecoveryPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Recovery plan not found")

    item = RecoveryProcurement(
        plan_id=plan_id,
        item=req.item,
        category=req.category,
        quantity=req.quantity,
        unit_cost=req.unit_cost,
        total_cost=round(req.quantity * req.unit_cost, 2),
        supplier=req.supplier,
        status=req.status,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {
        "id": item.id,
        "item": item.item,
        "category": item.category,
        "quantity": item.quantity,
        "unit_cost": item.unit_cost,
        "total_cost": item.total_cost,
        "supplier": item.supplier,
        "status": item.status,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


@router.get("/phases")
def get_lifecycle_phases():
    return LIFECYCLE_PHASES
