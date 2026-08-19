from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

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
    description: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    status: str
    raw_message: str | None = None
    acknowledged: bool = False
    created_at: datetime | None = None


def _alert_to_dict(a: Alert) -> dict:
    out = AlertOut.model_validate(a)
    out.acknowledged = a.status == "acknowledged"
    out.created_at = a.issued_at
    return out


# ── Endpoints ──────────────────────────────────────────────────────────


@router.get("")
def list_alerts(severity: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Alert)
    if severity:
        query = query.filter(Alert.severity == severity)
    alerts = query.all()
    return {"alerts": [_alert_to_dict(a) for a in alerts]}


@router.patch("/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = "acknowledged"
    db.commit()
    db.refresh(alert)
    return _alert_to_dict(alert)
