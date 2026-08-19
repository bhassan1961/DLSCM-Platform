from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.alert import Alert
from app.services.edxl import generate_cap_alert, generate_edxl_de, parse_edxl_message

router = APIRouter(prefix="/api/v1/edxl", tags=["edxl"])


class CAPGenerateRequest(BaseModel):
    title: str
    description: str
    severity: str = "moderate"
    urgency: str = "Immediate"
    certainty: str = "Observed"
    event_type: str = "Met"
    latitude: float | None = None
    longitude: float | None = None
    radius_km: float | None = 50.0
    expires_hours: int = 24


class EDXLWrapRequest(BaseModel):
    content_xml: str
    distribution_type: str = "Report"
    keywords: list[str] | None = None


@router.post("/cap/generate")
def cap_generate(req: CAPGenerateRequest):
    xml = generate_cap_alert(
        title=req.title,
        description=req.description,
        severity=req.severity,
        urgency=req.urgency,
        certainty=req.certainty,
        event_type=req.event_type,
        latitude=req.latitude,
        longitude=req.longitude,
        radius_km=req.radius_km,
        expires_hours=req.expires_hours,
    )
    return {"xml": xml, "format": "CAP 1.2"}


@router.post("/wrap-alert/{alert_id}")
def wrap_alert_in_edxl(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    cap_xml = generate_cap_alert(
        title=alert.title,
        description=alert.description or "",
        severity=alert.severity,
        latitude=alert.latitude,
        longitude=alert.longitude,
    )

    edxl_xml = generate_edxl_de(
        content_xml=cap_xml,
        distribution_type="Alert",
        keywords=[alert.alert_type, alert.severity],
        target_areas=[{"circle": f"{alert.latitude},{alert.longitude} 50"}]
        if alert.latitude
        else None,
    )

    return {
        "alert_id": alert_id,
        "cap_xml": cap_xml,
        "edxl_xml": edxl_xml,
        "format": "EDXL-DE 2.0 wrapping CAP 1.2",
    }


@router.post("/wrap-sitrep")
def wrap_sitrep_in_edxl(req: EDXLWrapRequest):
    edxl_xml = generate_edxl_de(
        content_xml=req.content_xml,
        distribution_type=req.distribution_type,
        keywords=req.keywords,
    )
    return {"edxl_xml": edxl_xml, "format": "EDXL-DE 2.0"}


@router.post("/parse")
async def parse_message(request: Request):
    body = await request.body()
    xml_text = body.decode("utf-8")
    if not xml_text.strip():
        raise HTTPException(status_code=400, detail="Empty XML body")
    result = parse_edxl_message(xml_text)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
