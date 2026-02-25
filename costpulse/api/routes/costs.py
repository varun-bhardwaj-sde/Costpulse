"""Cost data API endpoints."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from costpulse.api.deps import get_db
from costpulse.models.cost_record import CostRecord

router = APIRouter()


@router.get("/")
async def list_costs(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    workspace_id: Optional[str] = None,
    sku_name: Optional[str] = None,
    user_email: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Query cost records with filters."""
    query = select(CostRecord).order_by(CostRecord.usage_date.desc())

    if start_date:
        query = query.where(CostRecord.usage_date >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.where(CostRecord.usage_date <= datetime.fromisoformat(end_date))
    if workspace_id:
        query = query.where(CostRecord.workspace_id == workspace_id)
    if sku_name:
        query = query.where(CostRecord.sku_name == sku_name)
    if user_email:
        query = query.where(CostRecord.user_email == user_email)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    result = await db.execute(query.limit(limit).offset(offset))
    records = result.scalars().all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": [
            {
                "id": str(r.id),
                "usage_date": r.usage_date.isoformat(),
                "workspace_id": r.workspace_id,
                "sku_name": r.sku_name,
                "cloud": r.cloud,
                "dbu_count": r.dbu_count,
                "dbu_rate": r.dbu_rate,
                "cost_usd": round(r.cost_usd, 4),
                "cluster_id": r.cluster_id,
                "job_id": r.job_id,
                "user_email": r.user_email,
                "tags": r.tags,
            }
            for r in records
        ],
    }


@router.get("/summary")
async def cost_summary(
    days: int = Query(30, ge=1, le=365),
    workspace_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get a cost summary for the specified period."""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    query = select(
        func.sum(CostRecord.cost_usd).label("total_cost"),
        func.sum(CostRecord.dbu_count).label("total_dbu"),
        func.avg(CostRecord.cost_usd).label("avg_cost_per_record"),
        func.count().label("total_records"),
        func.min(CostRecord.usage_date).label("earliest"),
        func.max(CostRecord.usage_date).label("latest"),
    ).where(CostRecord.usage_date >= start_date)

    if workspace_id:
        query = query.where(CostRecord.workspace_id == workspace_id)

    result = await db.execute(query)
    row = result.one()

    total_cost = float(row.total_cost or 0)
    return {
        "period_days": days,
        "total_cost": round(total_cost, 2),
        "total_dbu": round(float(row.total_dbu or 0), 2),
        "avg_daily_cost": round(total_cost / days, 2) if days > 0 else 0,
        "avg_cost_per_record": round(float(row.avg_cost_per_record or 0), 4),
        "total_records": int(row.total_records or 0),
        "earliest_date": row.earliest.isoformat() if row.earliest else None,
        "latest_date": row.latest.isoformat() if row.latest else None,
    }


@router.get("/by-date")
async def costs_by_date(
    days: int = Query(30, ge=1, le=365),
    workspace_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get daily cost totals."""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    query = (
        select(
            func.date_trunc("day", CostRecord.usage_date).label("date"),
            func.sum(CostRecord.cost_usd).label("cost"),
            func.sum(CostRecord.dbu_count).label("dbu"),
            func.count().label("records"),
        )
        .where(CostRecord.usage_date >= start_date)
        .group_by(func.date_trunc("day", CostRecord.usage_date))
        .order_by(func.date_trunc("day", CostRecord.usage_date))
    )
    if workspace_id:
        query = query.where(CostRecord.workspace_id == workspace_id)

    result = await db.execute(query)
    return {
        "data": [
            {
                "date": row.date.isoformat(),
                "cost": round(float(row.cost), 2),
                "dbu": round(float(row.dbu), 2),
                "records": row.records,
            }
            for row in result.all()
        ]
    }
