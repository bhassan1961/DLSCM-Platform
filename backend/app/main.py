from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.seed import seed_all
import app.models as _models  # noqa: F401 — ensure all models are registered with Base.metadata
from app.routers import (
    auth,
    inventory,
    supply_requests,
    disasters,
    alerts,
    shipments,
    dashboard,
    coordination,
    forecasting,
    routing,
    reports,
    marketplace,
    simulation,
    risk,
    sitrep,
)


@asynccontextmanager
async def lifespan(application: FastAPI):
    # Startup: create tables and seed data
    Base.metadata.create_all(bind=engine)
    seed_all()
    yield
    # Shutdown: nothing to clean up


app = FastAPI(
    title="DLSCM API",
    description="Disaster Logistics & Supply Chain Management Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3100"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth.router)
app.include_router(inventory.router)
app.include_router(supply_requests.router)
app.include_router(disasters.router)
app.include_router(alerts.router)
app.include_router(shipments.router)
app.include_router(dashboard.router)
app.include_router(coordination.router)
app.include_router(forecasting.router)
app.include_router(routing.router)
app.include_router(reports.router)
app.include_router(marketplace.router)
app.include_router(simulation.router)
app.include_router(risk.router)
app.include_router(sitrep.router)


@app.get("/")
def root():
    return {"message": "DLSCM API is running", "docs": "/docs"}
