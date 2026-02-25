"""Cost allocation API endpoints."""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from costpulse.api.deps import get_db
from costpulse.models.allocation import AllocationRule, CostAllocation
from costpulse.services.cost_allocation import CostAllocationService

router = APIRouter()


class AllocationRuleCreate(BaseModel):
    name: str
    team_id: uuid.UUID
    rule_type: str
    conditions: dict
    priority: int = 100
    description: Optional[str] = None


@router.post("/run")
async def run_allocation(
    period_start: str = Query(...),
    period_end: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Run cost allocation for a given period."""
    service = CostAllocationService(db)
    results = await service.allocate_costs(
        period_start=datetime.fromisoformat(period_start),
        period_end=datetime.fromisoformat(period_end),
    )
    return {"status": "completed", "allocations": results}


@router.get("/")
async def list_allocations(
    team_id: Optional[str] = None,
    period_start: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List cost allocations."""
    query = select(CostAllocation).order_by(CostAllocation.period_start.desc()).limit(limit)
    if team_id:
        query = query.where(CostAllocation.team_id == uuid.UUID(team_id))
    if period_start:
        query = query.where(CostAllocation.period_start >= datetime.fromisoformat(period_start))

    result = await db.execute(query)
    allocations = result.scalars().all()

    return {
        "data": [
            {
                "id": str(a.id),
                "team_id": str(a.team_id),
                "period_start": a.period_start.isoformat(),
                "period_end": a.period_end.isoformat(),
                "total_cost": round(a.total_cost, 2),
                "dbu_cost": round(a.dbu_cost, 2),
                "compute_cost": round(a.compute_cost, 2),
                "breakdown": a.breakdown,
                "allocation_method": a.allocation_method,
            }
            for a in allocations
        ]
    }


# Allocation Rules CRUD


@router.get("/rules")
async def list_rules(db: AsyncSession = Depends(get_db)):
    """List all allocation rules."""
    result = await db.execute(select(AllocationRule).order_by(AllocationRule.priority))
    rules = result.scalars().all()
    return {
        "data": [
            {
                "id": str(r.id),
                "name": r.name,
                "team_id": str(r.team_id),
                "rule_type": r.rule_type,
                "conditions": r.conditions,
                "priority": r.priority,
                "is_active": r.is_active,
                "description": r.description,
            }
            for r in rules
        ]
    }


@router.post("/rules")
async def create_rule(data: AllocationRuleCreate, db: AsyncSession = Depends(get_db)):
    """Create an allocation rule."""
    rule = AllocationRule(**data.model_dump())
    db.add(rule)
    await db.flush()
    return {"id": str(rule.id), "name": rule.name}


@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete an allocation rule."""
    result = await db.execute(select(AllocationRule).where(AllocationRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await db.delete(rule)
    await db.flush()
    return {"status": "deleted"}
