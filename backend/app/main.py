from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

import app.models as _models  # noqa: F401
from app.auth import require_auth
from app.database import Base, engine
from app.logging_config import get_logger, setup_logging
from app.routers import (
    alerts,
    anomalies,
    audit,
    auth,
    compliance,
    coordination,
    dashboard,
    disasters,
    donations,
    edxl,
    forecasting,
    intelligence,
    inventory,
    kits,
    marketplace,
    prepositioning,
    recovery,
    reports,
    risk,
    routing,
    shipments,
    simulation,
    sitrep,
    suppliers,
    supply_requests,
    sync,
)
from app.security import (
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)
from app.seed import seed_all
from app.websocket_manager import ws_manager

logger = get_logger("app")


@asynccontextmanager
async def lifespan(application: FastAPI):
    setup_logging()
    logger.info("DLSCM API starting up")
    Base.metadata.create_all(bind=engine)
    seed_all()
    logger.info("Database initialized and seeded")
    yield
    logger.info("DLSCM API shutting down")


app = FastAPI(
    title="DLSCM API",
    description="Disaster Logistics & Supply Chain Management Platform",
    version="0.2.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3100"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_auth_dep = [Depends(require_auth)]

app.include_router(auth.router)

app.include_router(inventory.router, dependencies=_auth_dep)
app.include_router(supply_requests.router, dependencies=_auth_dep)
app.include_router(disasters.router, dependencies=_auth_dep)
app.include_router(alerts.router, dependencies=_auth_dep)
app.include_router(shipments.router, dependencies=_auth_dep)
app.include_router(dashboard.router, dependencies=_auth_dep)
app.include_router(coordination.router, dependencies=_auth_dep)
app.include_router(forecasting.router, dependencies=_auth_dep)
app.include_router(routing.router, dependencies=_auth_dep)
app.include_router(reports.router, dependencies=_auth_dep)
app.include_router(marketplace.router, dependencies=_auth_dep)
app.include_router(simulation.router, dependencies=_auth_dep)
app.include_router(risk.router, dependencies=_auth_dep)
app.include_router(sitrep.router, dependencies=_auth_dep)
app.include_router(suppliers.router, dependencies=_auth_dep)
app.include_router(kits.router, dependencies=_auth_dep)
app.include_router(audit.router, dependencies=_auth_dep)
app.include_router(donations.router, dependencies=_auth_dep)
app.include_router(compliance.router, dependencies=_auth_dep)
app.include_router(intelligence.router, dependencies=_auth_dep)
app.include_router(prepositioning.router, dependencies=_auth_dep)
app.include_router(edxl.router, dependencies=_auth_dep)
app.include_router(recovery.router, dependencies=_auth_dep)
app.include_router(sync.router, dependencies=_auth_dep)
app.include_router(anomalies.router, dependencies=_auth_dep)


# ── WebSocket endpoint ───────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# ── Audit Logging Middleware ──────────────────────────────────────────
import json

from starlette.requests import Request
from starlette.responses import Response

from app.auth import decode_token
from app.database import SessionLocal
from app.models.audit_log import AuditLog


@app.middleware("http")
async def audit_logging_middleware(request: Request, call_next):
    if request.method in ("GET", "HEAD", "OPTIONS") or not request.url.path.startswith(
        "/api/"
    ):
        return await call_next(request)

    body_bytes = await request.body()
    request_body = None
    if body_bytes:
        try:
            request_body = json.loads(body_bytes)
            if isinstance(request_body, dict):
                request_body = {
                    k: v
                    for k, v in request_body.items()
                    if k not in ("password", "current_password", "new_password")
                }
        except (json.JSONDecodeError, UnicodeDecodeError):
            request_body = None

    response: Response = await call_next(request)

    response_body = b""
    resource_id = None
    async for chunk in response.body_iterator:
        if isinstance(chunk, str):
            response_body += chunk.encode()
        else:
            response_body += chunk
    try:
        resp_json = json.loads(response_body)
        if isinstance(resp_json, dict):
            resource_id = resp_json.get("id")
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass

    method_action_map = {
        "POST": "create",
        "PATCH": "update",
        "PUT": "update",
        "DELETE": "delete",
    }
    action = method_action_map.get(request.method, request.method.lower())

    path_parts = request.url.path.strip("/").split("/")
    resource_type = path_parts[2] if len(path_parts) > 2 else "unknown"

    if resource_id is None and len(path_parts) > 3:
        try:
            resource_id = int(path_parts[3])
        except (ValueError, IndexError):
            pass

    user_email = None
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        payload = decode_token(token)
        if payload:
            user_email = payload.get("sub")

    try:
        db = SessionLocal()
        log_entry = AuditLog(
            user_email=user_email,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "request_body": request_body,
            },
            ip_address=request.client.host if request.client else None,
        )
        db.add(log_entry)
        db.commit()
    except Exception:
        logger.debug("Audit log write failed", exc_info=True)
    finally:
        db.close()

    return Response(
        content=response_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
    )


@app.get("/")
def root():
    return {"message": "DLSCM API is running", "docs": "/docs"}
