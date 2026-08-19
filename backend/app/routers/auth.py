from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session, joinedload

from app.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    require_auth,
    verify_password,
)
from app.database import get_db
from app.models.user import Organization, User

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
    created_at: datetime | None = None
    organization: OrganizationOut | None = None


class LoginRequest(BaseModel):
    email: str
    password: str | None = None


class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str
    role: str = "field_coordinator"
    organization_id: int


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# ── Endpoints ──────────────────────────────────────────────────────────


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .options(joinedload(User.organization))
        .filter(User.email == req.email)
        .first()
    )
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")

    if user.password_hash and (
        not req.password or not verify_password(req.password, user.password_hash)
    ):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    # else: demo user without password — allow login for backward compatibility

    token_data = {"sub": user.email, "role": user.role, "org_id": user.organization_id}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserOut.model_validate(user),
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    org = db.query(Organization).filter(Organization.id == req.organization_id).first()
    if not org:
        raise HTTPException(status_code=400, detail="Organization not found")

    user = User(
        email=req.email,
        name=req.name,
        password_hash=hash_password(req.password),
        role=req.role,
        organization_id=req.organization_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    user = (
        db.query(User)
        .options(joinedload(User.organization))
        .filter(User.id == user.id)
        .first()
    )
    token_data = {"sub": user.email, "role": user.role, "org_id": user.organization_id}

    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        user=UserOut.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(req: RefreshRequest, db: Session = Depends(get_db)):
    payload = decode_token(req.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    email = payload.get("sub")
    user = (
        db.query(User)
        .options(joinedload(User.organization))
        .filter(User.email == email)
        .first()
    )
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    token_data = {"sub": user.email, "role": user.role, "org_id": user.organization_id}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(require_auth)):
    return UserOut.model_validate(user)


@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    if user.password_hash and not verify_password(
        req.current_password, user.password_hash
    ):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.password_hash = hash_password(req.new_password)
    db.commit()
    return {"message": "Password changed successfully"}


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).options(joinedload(User.organization)).all()
    return [UserOut.model_validate(u) for u in users]
