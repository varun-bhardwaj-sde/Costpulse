"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from costpulse.api.routes import (
    alerts,
    allocations,
    clusters,
    costs,
    dashboard,
    forecasts,
    recommendations,
    reports,
    tags,
    teams,
    workspaces,
)
from costpulse.models.base import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize DB on startup."""
    await init_db()
    yield


app = FastAPI(
    title="CostPulse FinOps Platform",
    description="Self-service FinOps-in-a-box for Databricks customers",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(costs.router, prefix="/api/v1/costs", tags=["Costs"])
app.include_router(workspaces.router, prefix="/api/v1/workspaces", tags=["Workspaces"])
app.include_router(teams.router, prefix="/api/v1/teams", tags=["Teams"])
app.include_router(allocations.router, prefix="/api/v1/allocations", tags=["Allocations"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["Recommendations"])
app.include_router(forecasts.router, prefix="/api/v1/forecasts", tags=["Forecasts"])
app.include_router(tags.router, prefix="/api/v1/tags", tags=["Tags"])
app.include_router(clusters.router, prefix="/api/v1/clusters", tags=["Clusters"])


@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "service": "costpulse"}
