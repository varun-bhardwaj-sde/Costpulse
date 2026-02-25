"""Cost forecasting API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from costpulse.api.deps import get_db
from costpulse.services.forecast_service import ForecastService

router = APIRouter()


@router.post("/generate")
async def generate_forecast(
    horizon_days: int = Query(30, ge=7, le=90),
    workspace_id: Optional[str] = None,
    team_id: Optional[str] = None,
    granularity: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    db: AsyncSession = Depends(get_db),
):
    """Generate cost forecasts for the next N days."""
    service = ForecastService(db)
    forecasts = await service.generate_forecast(
        horizon_days=horizon_days,
        workspace_id=workspace_id,
        team_id=team_id,
        granularity=granularity,
    )
    return {
        "status": "completed",
        "horizon_days": horizon_days,
        "data_points": len(forecasts),
        "data": [
            {
                "date": f["date"].isoformat() if hasattr(f["date"], "isoformat") else str(f["date"]),
                "predicted_cost": round(f["predicted_cost"], 2),
                "lower_bound": round(f["lower_bound"], 2),
                "upper_bound": round(f["upper_bound"], 2),
                "model": f.get("model", "unknown"),
            }
            for f in forecasts
        ],
    }


@router.get("/summary")
async def forecast_summary(
    horizon_days: int = Query(30, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Get forecast summary."""
    service = ForecastService(db)
    return await service.get_forecast_summary(horizon_days=horizon_days)
