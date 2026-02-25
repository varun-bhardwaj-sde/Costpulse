"""Job run model for tracking Databricks job costs."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from costpulse.models.base import Base


class JobRun(Base):
    """Databricks job run metadata and costs."""

    __tablename__ = "job_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    job_name: Mapped[str] = mapped_column(String(255), nullable=True)
    workspace_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    creator_email: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    cluster_id: Mapped[str] = mapped_column(String(255), nullable=True)
    run_type: Mapped[str] = mapped_column(String(50), nullable=True)  # JOB_RUN, WORKFLOW_RUN
    state: Mapped[str] = mapped_column(String(50), nullable=True)
    result_state: Mapped[str] = mapped_column(String(50), nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    dbu_consumed: Mapped[float] = mapped_column(Float, default=0.0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    num_tasks: Mapped[int] = mapped_column(Integer, default=1)
    tags: Mapped[dict] = mapped_column(JSONB, default=dict)
    schedule: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
