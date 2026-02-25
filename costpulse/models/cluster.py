"""Cluster metadata model for tracking compute resources."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from costpulse.models.base import Base


class ClusterInfo(Base):
    """Databricks cluster metadata and utilization."""

    __tablename__ = "clusters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cluster_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    cluster_name: Mapped[str] = mapped_column(String(255), nullable=False)
    workspace_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    creator_email: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    cluster_type: Mapped[str] = mapped_column(String(50), nullable=True)  # all-purpose, job, sql
    state: Mapped[str] = mapped_column(String(50), default="UNKNOWN")
    node_type: Mapped[str] = mapped_column(String(100), nullable=True)
    driver_node_type: Mapped[str] = mapped_column(String(100), nullable=True)
    num_workers: Mapped[int] = mapped_column(Integer, default=0)
    autoscale_min: Mapped[int] = mapped_column(Integer, nullable=True)
    autoscale_max: Mapped[int] = mapped_column(Integer, nullable=True)
    spark_version: Mapped[str] = mapped_column(String(100), nullable=True)
    photon_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_termination_minutes: Mapped[int] = mapped_column(Integer, nullable=True)
    avg_cpu_utilization: Mapped[float] = mapped_column(Float, nullable=True)
    avg_memory_utilization: Mapped[float] = mapped_column(Float, nullable=True)
    total_dbu_consumed: Mapped[float] = mapped_column(Numeric(18, 6), default=0.0)
    total_cost_usd: Mapped[float] = mapped_column(Numeric(18, 6), default=0.0)
    total_runtime_hours: Mapped[float] = mapped_column(Float, default=0.0)
    idle_time_hours: Mapped[float] = mapped_column(Float, default=0.0)
    is_idle: Mapped[bool] = mapped_column(Boolean, default=False)
    tags: Mapped[dict] = mapped_column(JSONB, default=dict)
    last_active_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
