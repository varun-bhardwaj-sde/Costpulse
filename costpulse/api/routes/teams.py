"""Team management API endpoints."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from costpulse.api.deps import get_db
from costpulse.models.team import Team, TeamMember

router = APIRouter()


class TeamCreate(BaseModel):
    name: str
    department: Optional[str] = None
    cost_center: Optional[str] = None
    manager_email: Optional[str] = None
    description: Optional[str] = None
    tag_patterns: Optional[dict] = None


class TeamMemberCreate(BaseModel):
    email: str
    display_name: Optional[str] = None
    role: str = "member"
    databricks_user_id: Optional[str] = None


@router.get("/")
async def list_teams(db: AsyncSession = Depends(get_db)):
    """List all teams."""
    result = await db.execute(
        select(Team).options(selectinload(Team.members)).order_by(Team.name)
    )
    teams = result.scalars().all()
    return {
        "data": [
            {
                "id": str(t.id),
                "name": t.name,
                "department": t.department,
                "cost_center": t.cost_center,
                "manager_email": t.manager_email,
                "member_count": len(t.members) if t.members else 0,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in teams
        ]
    }


@router.post("/")
async def create_team(data: TeamCreate, db: AsyncSession = Depends(get_db)):
    """Create a new team."""
    existing = await db.execute(select(Team).where(Team.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Team already exists")

    team = Team(**data.model_dump(exclude_none=True))
    db.add(team)
    await db.flush()
    return {"id": str(team.id), "name": team.name}


@router.get("/{team_id}")
async def get_team(team_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get team details with members."""
    result = await db.execute(
        select(Team).options(selectinload(Team.members)).where(Team.id == team_id)
    )
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    return {
        "id": str(team.id),
        "name": team.name,
        "department": team.department,
        "cost_center": team.cost_center,
        "manager_email": team.manager_email,
        "description": team.description,
        "tag_patterns": team.tag_patterns,
        "members": [
            {
                "id": str(m.id),
                "email": m.email,
                "display_name": m.display_name,
                "role": m.role,
            }
            for m in (team.members or [])
        ],
    }


@router.patch("/{team_id}")
async def update_team(team_id: uuid.UUID, data: TeamCreate, db: AsyncSession = Depends(get_db)):
    """Update team details."""
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(team, key, value)
    await db.flush()
    return {"status": "updated", "id": str(team.id)}


@router.delete("/{team_id}")
async def delete_team(team_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete a team."""
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    await db.delete(team)
    await db.flush()
    return {"status": "deleted"}


@router.post("/{team_id}/members")
async def add_team_member(
    team_id: uuid.UUID, data: TeamMemberCreate, db: AsyncSession = Depends(get_db)
):
    """Add a member to a team."""
    result = await db.execute(select(Team).where(Team.id == team_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Team not found")

    member = TeamMember(team_id=team_id, **data.model_dump(exclude_none=True))
    db.add(member)
    await db.flush()
    return {"id": str(member.id), "email": member.email}


@router.delete("/{team_id}/members/{member_id}")
async def remove_team_member(
    team_id: uuid.UUID, member_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    """Remove a member from a team."""
    result = await db.execute(
        select(TeamMember).where(TeamMember.id == member_id, TeamMember.team_id == team_id)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    await db.delete(member)
    await db.flush()
    return {"status": "deleted"}
