from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.user import User, Organization

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ── Schemas ────────────────────────────────────────────────────────────

class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    org_type: str
    country: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    role: str
    organization_id: int
    is_active: bool
    created_at: Optional[datetime] = None
    organization: Optional[OrganizationOut] = None


class LoginRequest(BaseModel):
    email: str


class LoginResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user: UserOut
    message: str


# ── Endpoints ──────────────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .options(joinedload(User.organization))
        .filter(User.email == req.email)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")
    return LoginResponse(user=UserOut.model_validate(user), message="Login successful")


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    users = (
        db.query(User)
        .options(joinedload(User.organization))
        .all()
    )
    return [UserOut.model_validate(u) for u in users]
