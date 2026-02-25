"""Report model for generated showback/chargeback reports."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from costpulse.models.base import Base


class Report(Base):
    """Generated cost reports (PDF/Excel)."""

    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # showback, chargeback, executive, team
    format: Mapped[str] = mapped_column(String(20), nullable=False)  # pdf, excel, csv
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )  # pending, generating, completed, failed
    parameters: Mapped[dict] = mapped_column(JSONB, default=dict)
    summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    generated_by: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
