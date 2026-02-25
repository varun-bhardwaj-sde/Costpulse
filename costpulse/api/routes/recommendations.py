"""Recommendation API endpoints."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from costpulse.api.deps import get_db
from costpulse.services.recommendation_service import RecommendationService

router = APIRouter()


class StatusUpdate(BaseModel):
    status: str  # accepted, dismissed, implemented


@router.get("/")
async def list_recommendations(
    status: Optional[str] = Query("open"),
    recommendation_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List optimization recommendations."""
    service = RecommendationService(db)
    recs = await service.list_recommendations(
        status=status,
        recommendation_type=recommendation_type,
        limit=limit,
    )
    return {
        "data": [
            {
                "id": str(r.id),
                "type": r.recommendation_type,
                "severity": r.severity,
                "title": r.title,
                "description": r.description,
                "workspace_id": r.workspace_id,
                "resource_id": r.resource_id,
                "resource_type": r.resource_type,
                "current_cost": r.current_cost,
                "estimated_savings": r.estimated_savings,
                "details": r.details,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in recs
        ]
    }


@router.post("/generate")
async def generate_recommendations(db: AsyncSession = Depends(get_db)):
    """Trigger recommendation generation."""
    service = RecommendationService(db)
    recs = await service.generate_all_recommendations()
    return {"status": "completed", "count": len(recs), "recommendations": recs}


@router.patch("/{rec_id}/status")
async def update_recommendation_status(
    rec_id: uuid.UUID, data: StatusUpdate, db: AsyncSession = Depends(get_db)
):
    """Update recommendation status (accept, dismiss, implement)."""
    service = RecommendationService(db)
    rec = await service.update_recommendation_status(rec_id, data.status)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return {"status": "updated", "id": str(rec.id), "new_status": rec.status}
