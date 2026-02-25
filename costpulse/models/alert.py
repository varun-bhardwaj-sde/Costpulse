"""Alert configuration and history models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from costpulse.models.base import Base


class Alert(Base):
    """Alert configuration for budget thresholds and anomalies."""

    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    alert_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # budget_threshold, anomaly, idle_cluster, cost_spike
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
    )
    workspace_id: Mapped[str] = mapped_column(String(255), nullable=True)
    threshold_value: Mapped[float] = mapped_column(Float, nullable=True)
    threshold_type: Mapped[str] = mapped_column(
        String(50), default="absolute"
    )  # absolute, percentage
    notification_channels: Mapped[dict] = mapped_column(
        JSONB, default=lambda: {"slack": True, "email": True}
    )
    conditions: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    cooldown_minutes: Mapped[int] = mapped_column(default=60)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    team = relationship("Team", back_populates="alerts")
    history = relationship("AlertHistory", back_populates="alert", lazy="selectin")


class AlertHistory(Base):
    """History of fired alerts."""

    __tablename__ = "alert_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False
    )
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="triggered"
    )  # triggered, resolved, acknowledged
    current_value: Mapped[float] = mapped_column(Float, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=True)
    notification_sent: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Relationships
    alert = relationship("Alert", back_populates="history")
