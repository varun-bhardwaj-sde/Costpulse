"""Recommendation model for optimization suggestions."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from costpulse.models.base import Base


class Recommendation(Base):
    """AI-powered optimization recommendations."""

    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recommendation_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # idle_cluster, right_sizing, cost_anomaly, policy_enforcement
    severity: Mapped[str] = mapped_column(
        String(20), default="medium"
    )  # low, medium, high, critical
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    workspace_id: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    resource_id: Mapped[str] = mapped_column(String(255), nullable=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=True)  # cluster, job, warehouse
    current_cost: Mapped[float] = mapped_column(Float, nullable=True)
    estimated_savings: Mapped[float] = mapped_column(Float, nullable=True)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(
        String(50), default="open"
    )  # open, accepted, dismissed, implemented
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
