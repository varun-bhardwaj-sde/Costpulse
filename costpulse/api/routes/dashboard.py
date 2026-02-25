"""Dashboard API: aggregated cost overview endpoints."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from costpulse.api.deps import get_db
from costpulse.models.cluster import ClusterInfo
from costpulse.models.cost_record import CostRecord
from costpulse.models.recommendation import Recommendation

router = APIRouter()


@router.get("/overview")
async def get_overview(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get high-level cost overview for the dashboard."""
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)
    prev_start = start_date - timedelta(days=days)

    # Current period totals
    current = await db.execute(
        select(
            func.sum(CostRecord.cost_usd).label("total_cost"),
            func.sum(CostRecord.dbu_count).label("total_dbu"),
            func.count().label("record_count"),
        ).where(CostRecord.usage_date >= start_date)
    )
    current_row = current.one()

    # Previous period for comparison
    previous = await db.execute(
        select(func.sum(CostRecord.cost_usd).label("total_cost")).where(
            CostRecord.usage_date >= prev_start,
            CostRecord.usage_date < start_date,
        )
    )
    prev_cost = previous.scalar() or 0

    current_cost = float(current_row.total_cost or 0)
    cost_change_pct = ((current_cost - prev_cost) / prev_cost * 100) if prev_cost > 0 else 0

    # Active clusters
    active_clusters = await db.execute(
        select(func.count()).select_from(ClusterInfo).where(ClusterInfo.state == "RUNNING")
    )
    idle_clusters = await db.execute(
        select(func.count())
        .select_from(ClusterInfo)
        .where(ClusterInfo.state == "RUNNING", ClusterInfo.is_idle.is_(True))
    )

    # Open recommendations
    open_recs = await db.execute(
        select(func.count()).select_from(Recommendation).where(Recommendation.status == "open")
    )
    savings_result = await db.execute(
        select(func.sum(Recommendation.estimated_savings)).where(Recommendation.status == "open")
    )

    return {
        "period_days": days,
        "total_cost": current_cost,
        "total_dbu": float(current_row.total_dbu or 0),
        "record_count": int(current_row.record_count or 0),
        "cost_change_pct": round(cost_change_pct, 1),
        "prev_period_cost": float(prev_cost),
        "active_clusters": active_clusters.scalar() or 0,
        "idle_clusters": idle_clusters.scalar() or 0,
        "open_recommendations": open_recs.scalar() or 0,
        "potential_savings": float(savings_result.scalar() or 0),
    }


@router.get("/cost-trend")
async def get_cost_trend(
    days: int = Query(30, ge=1, le=365),
    granularity: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    db: AsyncSession = Depends(get_db),
):
    """Get cost trend data for charts."""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    trunc = {"daily": "day", "weekly": "week", "monthly": "month"}[granularity]

    result = await db.execute(
        select(
            func.date_trunc(trunc, CostRecord.usage_date).label("period"),
            func.sum(CostRecord.cost_usd).label("cost"),
            func.sum(CostRecord.dbu_count).label("dbu"),
        )
        .where(CostRecord.usage_date >= start_date)
        .group_by(func.date_trunc(trunc, CostRecord.usage_date))
        .order_by(func.date_trunc(trunc, CostRecord.usage_date))
    )

    return {
        "granularity": granularity,
        "data": [
            {
                "period": row.period.isoformat(),
                "cost": round(float(row.cost), 2),
                "dbu": round(float(row.dbu), 2),
            }
            for row in result.all()
        ],
    }


@router.get("/cost-by-workspace")
async def get_cost_by_workspace(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get cost breakdown by workspace."""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            CostRecord.workspace_id,
            func.sum(CostRecord.cost_usd).label("cost"),
            func.sum(CostRecord.dbu_count).label("dbu"),
            func.count().label("records"),
        )
        .where(CostRecord.usage_date >= start_date)
        .group_by(CostRecord.workspace_id)
        .order_by(func.sum(CostRecord.cost_usd).desc())
    )

    return {
        "data": [
            {
                "workspace_id": row.workspace_id,
                "cost": round(float(row.cost), 2),
                "dbu": round(float(row.dbu), 2),
                "records": row.records,
            }
            for row in result.all()
        ]
    }


@router.get("/cost-by-sku")
async def get_cost_by_sku(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get cost breakdown by SKU type."""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            CostRecord.sku_name,
            func.sum(CostRecord.cost_usd).label("cost"),
            func.sum(CostRecord.dbu_count).label("dbu"),
        )
        .where(CostRecord.usage_date >= start_date)
        .group_by(CostRecord.sku_name)
        .order_by(func.sum(CostRecord.cost_usd).desc())
    )

    return {
        "data": [
            {
                "sku": row.sku_name,
                "cost": round(float(row.cost), 2),
                "dbu": round(float(row.dbu), 2),
            }
            for row in result.all()
        ]
    }


@router.get("/cost-by-user")
async def get_cost_by_user(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get top users by cost."""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            CostRecord.user_email,
            func.sum(CostRecord.cost_usd).label("cost"),
            func.sum(CostRecord.dbu_count).label("dbu"),
        )
        .where(
            CostRecord.usage_date >= start_date,
            CostRecord.user_email.isnot(None),
        )
        .group_by(CostRecord.user_email)
        .order_by(func.sum(CostRecord.cost_usd).desc())
        .limit(limit)
    )

    return {
        "data": [
            {
                "user": row.user_email,
                "cost": round(float(row.cost), 2),
                "dbu": round(float(row.dbu), 2),
            }
            for row in result.all()
        ]
    }


@router.get("/cost-by-job")
async def get_cost_by_job(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get top jobs by cost."""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            CostRecord.job_id,
            CostRecord.job_name,
            func.sum(CostRecord.cost_usd).label("cost"),
            func.sum(CostRecord.dbu_count).label("dbu"),
        )
        .where(
            CostRecord.usage_date >= start_date,
            CostRecord.job_id.isnot(None),
        )
        .group_by(CostRecord.job_id, CostRecord.job_name)
        .order_by(func.sum(CostRecord.cost_usd).desc())
        .limit(limit)
    )

    return {
        "data": [
            {
                "job_id": row.job_id,
                "job_name": row.job_name or f"Job {row.job_id}",
                "cost": round(float(row.cost), 2),
                "dbu": round(float(row.dbu), 2),
            }
            for row in result.all()
        ]
    }
