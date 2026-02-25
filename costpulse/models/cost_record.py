"""Cost record model — the core billing data table (TimescaleDB hypertable)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Index, String, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from costpulse.models.base import Base


class CostRecord(Base):
    """Raw cost records from Databricks system tables."""

    __tablename__ = "cost_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usage_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sku_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    cloud: Mapped[str] = mapped_column(String(50), nullable=True)
    usage_unit: Mapped[str] = mapped_column(String(50), default="DBU")
    dbu_count: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    dbu_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cluster_id: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    cluster_name: Mapped[str] = mapped_column(String(255), nullable=True)
    job_id: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    job_name: Mapped[str] = mapped_column(String(255), nullable=True)
    warehouse_id: Mapped[str] = mapped_column(String(255), nullable=True)
    user_email: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    tags: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_cost_records_date_workspace", "usage_date", "workspace_id"),
        Index("ix_cost_records_date_sku", "usage_date", "sku_name"),
        Index("ix_cost_records_user_date", "user_email", "usage_date"),
    )
