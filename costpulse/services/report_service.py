"""Report generation service for showback/chargeback reports."""

import csv
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from costpulse.models.allocation import CostAllocation
from costpulse.models.cost_record import CostRecord
from costpulse.models.report import Report
from costpulse.models.team import Team

logger = structlog.get_logger()

REPORTS_DIR = os.environ.get("REPORTS_DIR", "/tmp/costpulse_reports")

ALLOWED_REPORT_TYPES = {"showback", "chargeback", "executive", "team"}
ALLOWED_FORMATS = {"csv", "excel", "pdf"}


class ReportService:
    """Generate showback, chargeback, and executive cost reports."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def generate_report(
        self,
        report_type: str,
        format: str,
        period_start: datetime,
        period_end: datetime,
        parameters: Optional[Dict] = None,
    ) -> Report:
        """Generate a cost report.

        Args:
            report_type: showback, chargeback, executive, team
            format: csv, excel, pdf
            period_start: Report period start
            period_end: Report period end
            parameters: Additional report parameters

        Returns:
            Report record with file path
        """
        if report_type not in ALLOWED_REPORT_TYPES:
            raise ValueError(f"Invalid report_type: {report_type}")
        if format not in ALLOWED_FORMATS:
            raise ValueError(f"Invalid format: {format}")

        report = Report(
            name=f"{report_type.title()} Report {period_start.strftime('%Y-%m')}",
            report_type=report_type,
            format=format,
            period_start=period_start,
            period_end=period_end,
            status="generating",
            parameters=parameters or {},
        )
        self.session.add(report)
        await self.session.flush()

        try:
            # Gather report data
            data = await self._gather_report_data(report_type, period_start, period_end, parameters)
            report.summary = data.get("summary", {})

            # Generate file
            os.makedirs(REPORTS_DIR, exist_ok=True)
            file_path = os.path.join(
                REPORTS_DIR,
                f"{report_type}_{period_start.strftime('%Y%m%d')}_{str(report.id)[:8]}.{format}",
            )

            if format == "csv":
                self._generate_csv(data, file_path)
            elif format == "excel":
                self._generate_excel(data, file_path)
            elif format == "pdf":
                self._generate_pdf(data, file_path)

            report.file_path = file_path
            report.file_size_bytes = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            report.status = "completed"
            report.completed_at = datetime.utcnow()

            logger.info("Report generated", report_id=str(report.id), format=format)
        except Exception as e:
            report.status = "failed"
            logger.error("Report generation failed", error=str(e))
            raise

        await self.session.flush()
        return report

    async def _gather_report_data(
        self,
        report_type: str,
        period_start: datetime,
        period_end: datetime,
        parameters: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Gather data for report generation."""
        # Total costs
        cost_result = await self.session.execute(
            select(
                func.sum(CostRecord.cost_usd).label("total_cost"),
                func.sum(CostRecord.dbu_count).label("total_dbu"),
                func.count().label("record_count"),
            ).where(
                CostRecord.usage_date >= period_start,
                CostRecord.usage_date < period_end,
            )
        )
        totals = cost_result.one()

        # Costs by workspace
        ws_result = await self.session.execute(
            select(
                CostRecord.workspace_id,
                func.sum(CostRecord.cost_usd).label("cost"),
                func.sum(CostRecord.dbu_count).label("dbu"),
            )
            .where(
                CostRecord.usage_date >= period_start,
                CostRecord.usage_date < period_end,
            )
            .group_by(CostRecord.workspace_id)
            .order_by(func.sum(CostRecord.cost_usd).desc())
        )
        by_workspace = [
            {"workspace_id": r.workspace_id, "cost": float(r.cost), "dbu": float(r.dbu)}
            for r in ws_result.all()
        ]

        # Costs by SKU
        sku_result = await self.session.execute(
            select(
                CostRecord.sku_name,
                func.sum(CostRecord.cost_usd).label("cost"),
            )
            .where(
                CostRecord.usage_date >= period_start,
                CostRecord.usage_date < period_end,
            )
            .group_by(CostRecord.sku_name)
            .order_by(func.sum(CostRecord.cost_usd).desc())
        )
        by_sku = [{"sku": r.sku_name, "cost": float(r.cost)} for r in sku_result.all()]

        # Costs by user
        user_result = await self.session.execute(
            select(
                CostRecord.user_email,
                func.sum(CostRecord.cost_usd).label("cost"),
            )
            .where(
                CostRecord.usage_date >= period_start,
                CostRecord.usage_date < period_end,
                CostRecord.user_email.isnot(None),
            )
            .group_by(CostRecord.user_email)
            .order_by(func.sum(CostRecord.cost_usd).desc())
            .limit(50)
        )
        by_user = [{"user": r.user_email, "cost": float(r.cost)} for r in user_result.all()]

        # Team allocations (for chargeback/showback)
        team_data = []
        if report_type in ("showback", "chargeback"):
            alloc_result = await self.session.execute(
                select(CostAllocation, Team)
                .join(Team, CostAllocation.team_id == Team.id)
                .where(
                    CostAllocation.period_start >= period_start,
                    CostAllocation.period_end <= period_end,
                )
            )
            for alloc, team in alloc_result.all():
                team_data.append(
                    {
                        "team": team.name,
                        "department": team.department,
                        "cost_center": team.cost_center,
                        "total_cost": alloc.total_cost,
                        "dbu_cost": alloc.dbu_cost,
                        "compute_cost": alloc.compute_cost,
                    }
                )

        # Daily trend
        daily_result = await self.session.execute(
            select(
                func.date_trunc("day", CostRecord.usage_date).label("day"),
                func.sum(CostRecord.cost_usd).label("cost"),
            )
            .where(
                CostRecord.usage_date >= period_start,
                CostRecord.usage_date < period_end,
            )
            .group_by(func.date_trunc("day", CostRecord.usage_date))
            .order_by(func.date_trunc("day", CostRecord.usage_date))
        )
        daily_trend = [
            {"date": r.day.isoformat(), "cost": float(r.cost)} for r in daily_result.all()
        ]

        return {
            "summary": {
                "total_cost": float(totals.total_cost or 0),
                "total_dbu": float(totals.total_dbu or 0),
                "record_count": int(totals.record_count or 0),
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
            },
            "by_workspace": by_workspace,
            "by_sku": by_sku,
            "by_user": by_user,
            "by_team": team_data,
            "daily_trend": daily_trend,
        }

    def _generate_csv(self, data: Dict, file_path: str) -> None:
        """Generate CSV report."""
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)

            # Summary section
            writer.writerow(["CostPulse Cost Report"])
            writer.writerow(
                ["Period", data["summary"]["period_start"], data["summary"]["period_end"]]
            )
            writer.writerow(["Total Cost (USD)", f"${data['summary']['total_cost']:,.2f}"])
            writer.writerow(["Total DBUs", f"{data['summary']['total_dbu']:,.0f}"])
            writer.writerow([])

            # By workspace
            writer.writerow(["Costs by Workspace"])
            writer.writerow(["Workspace ID", "Cost (USD)", "DBUs"])
            for ws in data["by_workspace"]:
                writer.writerow([ws["workspace_id"], f"${ws['cost']:,.2f}", f"{ws['dbu']:,.0f}"])
            writer.writerow([])

            # By SKU
            writer.writerow(["Costs by SKU"])
            writer.writerow(["SKU", "Cost (USD)"])
            for sku in data["by_sku"]:
                writer.writerow([sku["sku"], f"${sku['cost']:,.2f}"])
            writer.writerow([])

            # By user
            writer.writerow(["Top Users by Cost"])
            writer.writerow(["User", "Cost (USD)"])
            for user in data["by_user"]:
                writer.writerow([user["user"], f"${user['cost']:,.2f}"])

            # Team allocations
            if data.get("by_team"):
                writer.writerow([])
                writer.writerow(["Team Cost Allocations"])
                writer.writerow(
                    ["Team", "Department", "Cost Center", "Total Cost", "DBU Cost", "Compute Cost"]
                )
                for team in data["by_team"]:
                    writer.writerow(
                        [
                            team["team"],
                            team.get("department", ""),
                            team.get("cost_center", ""),
                            f"${team['total_cost']:,.2f}",
                            f"${team['dbu_cost']:,.2f}",
                            f"${team['compute_cost']:,.2f}",
                        ]
                    )

    def _generate_excel(self, data: Dict, file_path: str) -> None:
        """Generate Excel report using pandas."""
        try:
            import pandas as pd

            with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                # Summary
                summary_df = pd.DataFrame([data["summary"]])
                summary_df.to_excel(writer, sheet_name="Summary", index=False)

                # By workspace
                if data["by_workspace"]:
                    ws_df = pd.DataFrame(data["by_workspace"])
                    ws_df.to_excel(writer, sheet_name="By Workspace", index=False)

                # By SKU
                if data["by_sku"]:
                    sku_df = pd.DataFrame(data["by_sku"])
                    sku_df.to_excel(writer, sheet_name="By SKU", index=False)

                # By user
                if data["by_user"]:
                    user_df = pd.DataFrame(data["by_user"])
                    user_df.to_excel(writer, sheet_name="Top Users", index=False)

                # Team allocations
                if data.get("by_team"):
                    team_df = pd.DataFrame(data["by_team"])
                    team_df.to_excel(writer, sheet_name="Team Allocations", index=False)

                # Daily trend
                if data["daily_trend"]:
                    trend_df = pd.DataFrame(data["daily_trend"])
                    trend_df.to_excel(writer, sheet_name="Daily Trend", index=False)

        except ImportError:
            logger.warning("openpyxl not installed, falling back to CSV")
            self._generate_csv(data, file_path.replace(".excel", ".csv"))

    def _generate_pdf(self, data: Dict, file_path: str) -> None:
        """Generate PDF report. Falls back to CSV if PDF libraries unavailable."""
        # For MVP, generate a structured text file that can be converted to PDF
        # In production, use reportlab or weasyprint
        csv_path = file_path.replace(".pdf", ".csv")
        self._generate_csv(data, csv_path)
        # Rename to requested path
        os.rename(csv_path, file_path)
        logger.info("PDF report generated as CSV format", path=file_path)

    async def list_reports(
        self, report_type: Optional[str] = None, limit: int = 20
    ) -> List[Report]:
        """List generated reports."""
        query = select(Report).order_by(Report.created_at.desc()).limit(limit)
        if report_type:
            query = query.where(Report.report_type == report_type)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_report(self, report_id: uuid.UUID) -> Optional[Report]:
        """Get a specific report by ID."""
        result = await self.session.execute(select(Report).where(Report.id == report_id))
        return result.scalar_one_or_none()
