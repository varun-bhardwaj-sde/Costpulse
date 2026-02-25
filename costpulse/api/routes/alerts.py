"""Alert management API endpoints."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from costpulse.api.deps import get_db
from costpulse.models.alert import Alert
from costpulse.services.alert_service import AlertService

router = APIRouter()


class AlertCreate(BaseModel):
    name: str
    alert_type: str
    team_id: Optional[uuid.UUID] = None
    workspace_id: Optional[str] = None
    threshold_value: float
    threshold_type: str = "absolute"
    notification_channels: dict = {"slack": True, "email": True}
    conditions: dict = {}
    cooldown_minutes: int = 60
    description: Optional[str] = None


class AlertUpdate(BaseModel):
    name: Optional[str] = None
    threshold_value: Optional[float] = None
    notification_channels: Optional[dict] = None
    is_active: Optional[bool] = None
    cooldown_minutes: Optional[int] = None


@router.get("/")
async def list_alerts(
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all alert configurations."""
    query = select(Alert).order_by(Alert.created_at.desc())
    if is_active is not None:
        query = query.where(Alert.is_active == is_active)

    result = await db.execute(query)
    alerts = result.scalars().all()

    return {
        "data": [
            {
                "id": str(a.id),
                "name": a.name,
                "alert_type": a.alert_type,
                "team_id": str(a.team_id) if a.team_id else None,
                "workspace_id": a.workspace_id,
                "threshold_value": a.threshold_value,
                "threshold_type": a.threshold_type,
                "notification_channels": a.notification_channels,
                "is_active": a.is_active,
                "cooldown_minutes": a.cooldown_minutes,
                "description": a.description,
            }
            for a in alerts
        ]
    }


@router.post("/")
async def create_alert(data: AlertCreate, db: AsyncSession = Depends(get_db)):
    """Create a new alert configuration."""
    service = AlertService(db)
    alert = await service.create_alert(data.model_dump())
    return {"id": str(alert.id), "name": alert.name}


@router.patch("/{alert_id}")
async def update_alert(alert_id: uuid.UUID, data: AlertUpdate, db: AsyncSession = Depends(get_db)):
    """Update an alert configuration."""
    service = AlertService(db)
    alert = await service.update_alert(alert_id, data.model_dump(exclude_unset=True))
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "updated", "id": str(alert.id)}


@router.delete("/{alert_id}")
async def delete_alert(alert_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete an alert."""
    service = AlertService(db)
    deleted = await service.delete_alert(alert_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "deleted"}


@router.post("/check")
async def check_alerts(db: AsyncSession = Depends(get_db)):
    """Manually trigger alert evaluation."""
    service = AlertService(db)
    triggered = await service.check_alerts()
    return {"triggered": triggered, "count": len(triggered)}


@router.get("/history")
async def alert_history(
    alert_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get alert firing history."""
    service = AlertService(db)
    history = await service.get_alert_history(
        alert_id=uuid.UUID(alert_id) if alert_id else None,
        limit=limit,
    )
    return {
        "data": [
            {
                "id": str(h.id),
                "alert_id": str(h.alert_id),
                "triggered_at": h.triggered_at.isoformat() if h.triggered_at else None,
                "resolved_at": h.resolved_at.isoformat() if h.resolved_at else None,
                "status": h.status,
                "current_value": h.current_value,
                "message": h.message,
            }
            for h in history
        ]
    }
