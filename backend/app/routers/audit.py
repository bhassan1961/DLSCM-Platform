from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit_log import AuditLog
from app.pagination import paginate_query

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_email: str | None = None
    action: str
    resource_type: str
    resource_id: int | None = None
    details: Any | None = None
    ip_address: str | None = None
    timestamp: datetime | None = None


@router.get("")
def list_audit_logs(
    resource_type: str | None = Query(None, description="Filter by resource type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(AuditLog)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    query = query.order_by(AuditLog.timestamp.desc())
    result = paginate_query(query, page, page_size)
    return {
        "logs": [
            AuditLogOut.model_validate(log).model_dump() for log in result["items"]
        ],
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "pages": result["pages"],
    }
