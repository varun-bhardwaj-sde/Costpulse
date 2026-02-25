"""Report generation API endpoints."""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from costpulse.api.deps import get_db
from costpulse.services.report_service import ReportService

router = APIRouter()


class ReportRequest(BaseModel):
    report_type: str = "showback"  # showback, chargeback, executive, team
    format: str = "csv"  # csv, excel, pdf
    period_start: str
    period_end: str
    parameters: Optional[dict] = None


@router.post("/generate")
async def generate_report(data: ReportRequest, db: AsyncSession = Depends(get_db)):
    """Generate a new cost report."""
    service = ReportService(db)
    report = await service.generate_report(
        report_type=data.report_type,
        format=data.format,
        period_start=datetime.fromisoformat(data.period_start),
        period_end=datetime.fromisoformat(data.period_end),
        parameters=data.parameters,
    )
    return {
        "id": str(report.id),
        "name": report.name,
        "status": report.status,
        "file_path": report.file_path,
        "summary": report.summary,
    }


@router.get("/")
async def list_reports(
    report_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List generated reports."""
    service = ReportService(db)
    reports = await service.list_reports(report_type=report_type, limit=limit)
    return {
        "data": [
            {
                "id": str(r.id),
                "name": r.name,
                "report_type": r.report_type,
                "format": r.format,
                "period_start": r.period_start.isoformat(),
                "period_end": r.period_end.isoformat(),
                "status": r.status,
                "file_size_bytes": r.file_size_bytes,
                "summary": r.summary,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reports
        ]
    }


@router.get("/{report_id}")
async def get_report(report_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get report details."""
    service = ReportService(db)
    report = await service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {
        "id": str(report.id),
        "name": report.name,
        "report_type": report.report_type,
        "format": report.format,
        "status": report.status,
        "summary": report.summary,
        "file_path": report.file_path,
    }


@router.get("/{report_id}/download")
async def download_report(report_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Download a generated report file."""
    service = ReportService(db)
    report = await service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != "completed" or not report.file_path:
        raise HTTPException(status_code=400, detail="Report not ready for download")

    media_type_map = {
        "csv": "text/csv",
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pdf": "application/pdf",
    }
    return FileResponse(
        report.file_path,
        media_type=media_type_map.get(report.format, "application/octet-stream"),
        filename=f"{report.name.replace(' ', '_')}.{report.format}",
    )
