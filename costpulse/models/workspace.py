"""Workspace model for tracking Databricks workspaces."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from costpulse.models.base import Base


class Workspace(Base):
    """Databricks workspace metadata."""

    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    host: Mapped[str] = mapped_column(String(512), nullable=False)
    cloud: Mapped[str] = mapped_column(String(50), nullable=False)  # AWS, AZURE, GCP
    region: Mapped[str] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active")
    plan: Mapped[str] = mapped_column(String(50), nullable=True)  # STANDARD, PREMIUM, ENTERPRISE
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    num_users: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
