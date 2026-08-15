from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.alert import Alert

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


# ── Schemas ────────────────────────────────────────────────────────────

class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    alert_type: str
    severity: str
    title: str
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    status: str
    raw_message: Optional[str] = None


# ── Endpoints ──────────────────────────────────────────────────────────

@router.get("/", response_model=list[AlertOut])
def list_alerts(db: Session = Depends(get_db)):
    alerts = db.query(Alert).all()
    return [AlertOut.model_validate(a) for a in alerts]


@router.patch("/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = "acknowledged"
    db.commit()
    db.refresh(alert)
    return AlertOut.model_validate(alert)
