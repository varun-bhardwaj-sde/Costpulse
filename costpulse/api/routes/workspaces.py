"""Workspace management API endpoints."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from costpulse.api.deps import get_db
from costpulse.models.workspace import Workspace

router = APIRouter()


class WorkspaceCreate(BaseModel):
    workspace_id: str
    name: str
    host: str
    cloud: str
    region: Optional[str] = None
    plan: Optional[str] = None
    notes: Optional[str] = None


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    region: Optional[str] = None
    plan: Optional[str] = None
    notes: Optional[str] = None


@router.get("/")
async def list_workspaces(db: AsyncSession = Depends(get_db)):
    """List all registered workspaces."""
    result = await db.execute(select(Workspace).order_by(Workspace.name))
    workspaces = result.scalars().all()
    return {
        "data": [
            {
                "id": str(w.id),
                "workspace_id": w.workspace_id,
                "name": w.name,
                "host": w.host,
                "cloud": w.cloud,
                "region": w.region,
                "status": w.status,
                "plan": w.plan,
                "num_users": w.num_users,
                "created_at": w.created_at.isoformat() if w.created_at else None,
            }
            for w in workspaces
        ]
    }


@router.post("/")
async def create_workspace(data: WorkspaceCreate, db: AsyncSession = Depends(get_db)):
    """Register a new Databricks workspace."""
    existing = await db.execute(
        select(Workspace).where(Workspace.workspace_id == data.workspace_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Workspace already registered")

    workspace = Workspace(**data.model_dump())
    db.add(workspace)
    await db.flush()
    return {"id": str(workspace.id), "workspace_id": workspace.workspace_id, "name": workspace.name}


@router.get("/{workspace_id}")
async def get_workspace(workspace_id: str, db: AsyncSession = Depends(get_db)):
    """Get workspace details."""
    result = await db.execute(
        select(Workspace).where(Workspace.workspace_id == workspace_id)
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {
        "id": str(workspace.id),
        "workspace_id": workspace.workspace_id,
        "name": workspace.name,
        "host": workspace.host,
        "cloud": workspace.cloud,
        "region": workspace.region,
        "status": workspace.status,
        "plan": workspace.plan,
        "num_users": workspace.num_users,
        "notes": workspace.notes,
    }


@router.patch("/{workspace_id}")
async def update_workspace(
    workspace_id: str, data: WorkspaceUpdate, db: AsyncSession = Depends(get_db)
):
    """Update workspace details."""
    result = await db.execute(
        select(Workspace).where(Workspace.workspace_id == workspace_id)
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(workspace, key, value)
    await db.flush()
    return {"status": "updated", "workspace_id": workspace_id}


@router.delete("/{workspace_id}")
async def delete_workspace(workspace_id: str, db: AsyncSession = Depends(get_db)):
    """Remove a workspace registration."""
    result = await db.execute(
        select(Workspace).where(Workspace.workspace_id == workspace_id)
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    await db.delete(workspace)
    await db.flush()
    return {"status": "deleted", "workspace_id": workspace_id}
