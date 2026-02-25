"""Tag compliance API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from costpulse.api.deps import get_db
from costpulse.services.tag_compliance import TagComplianceService

router = APIRouter()


@router.get("/compliance")
async def check_tag_compliance(
    workspace_id: Optional[str] = None,
    required_tags: Optional[str] = Query(
        None, description="Comma-separated list of required tag keys"
    ),
    db: AsyncSession = Depends(get_db),
):
    """Check tag compliance across resources."""
    service = TagComplianceService(db)
    tags_list = required_tags.split(",") if required_tags else None
    report = await service.check_compliance(
        required_tags=tags_list,
        workspace_id=workspace_id,
    )
    return report
