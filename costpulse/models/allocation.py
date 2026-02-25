"""Cost allocation models for chargeback/showback."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from costpulse.models.base import Base


class AllocationRule(Base):
    """Rules for allocating costs to teams."""

    __tablename__ = "allocation_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    rule_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # tag_match, user_match, workspace_match, cluster_match, percentage
    conditions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    priority: Mapped[int] = mapped_column(default=100)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    team = relationship("Team", back_populates="allocation_rules")


class CostAllocation(Base):
    """Allocated costs per team for a given period."""

    __tablename__ = "cost_allocations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    dbu_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    compute_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    storage_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    breakdown: Mapped[dict] = mapped_column(JSONB, default=dict)
    rule_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
    allocation_method: Mapped[str] = mapped_column(String(50), default="rule_based")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    team = relationship("Team", back_populates="allocations")
