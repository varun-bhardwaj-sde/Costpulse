"""Cluster management API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from costpulse.api.deps import get_db
from costpulse.models.cluster import ClusterInfo

router = APIRouter()


@router.get("/")
async def list_clusters(
    workspace_id: Optional[str] = None,
    state: Optional[str] = None,
    is_idle: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List clusters with optional filters."""
    query = select(ClusterInfo).order_by(ClusterInfo.total_cost_usd.desc()).limit(limit)

    if workspace_id:
        query = query.where(ClusterInfo.workspace_id == workspace_id)
    if state:
        query = query.where(ClusterInfo.state == state)
    if is_idle is not None:
        query = query.where(ClusterInfo.is_idle == is_idle)

    result = await db.execute(query)
    clusters = result.scalars().all()

    return {
        "data": [
            {
                "id": str(c.id),
                "cluster_id": c.cluster_id,
                "cluster_name": c.cluster_name,
                "workspace_id": c.workspace_id,
                "creator_email": c.creator_email,
                "cluster_type": c.cluster_type,
                "state": c.state,
                "node_type": c.node_type,
                "num_workers": c.num_workers,
                "photon_enabled": c.photon_enabled,
                "auto_termination_minutes": c.auto_termination_minutes,
                "avg_cpu_utilization": c.avg_cpu_utilization,
                "avg_memory_utilization": c.avg_memory_utilization,
                "total_cost_usd": round(c.total_cost_usd, 2),
                "total_runtime_hours": round(c.total_runtime_hours, 1),
                "idle_time_hours": round(c.idle_time_hours, 1) if c.idle_time_hours else 0,
                "is_idle": c.is_idle,
                "tags": c.tags,
            }
            for c in clusters
        ]
    }


@router.get("/summary")
async def cluster_summary(db: AsyncSession = Depends(get_db)):
    """Get cluster fleet summary."""
    total = await db.execute(select(func.count()).select_from(ClusterInfo))
    running = await db.execute(
        select(func.count()).select_from(ClusterInfo).where(ClusterInfo.state == "RUNNING")
    )
    idle = await db.execute(
        select(func.count())
        .select_from(ClusterInfo)
        .where(ClusterInfo.is_idle.is_(True), ClusterInfo.state == "RUNNING")
    )
    total_cost = await db.execute(select(func.sum(ClusterInfo.total_cost_usd)))
    total_idle_hours = await db.execute(
        select(func.sum(ClusterInfo.idle_time_hours)).where(ClusterInfo.is_idle.is_(True))
    )

    return {
        "total_clusters": total.scalar() or 0,
        "running": running.scalar() or 0,
        "idle": idle.scalar() or 0,
        "total_cost": round(float(total_cost.scalar() or 0), 2),
        "total_idle_hours": round(float(total_idle_hours.scalar() or 0), 1),
    }
