"""Alert service for budget thresholds and notifications."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from costpulse.models.alert import Alert, AlertHistory
from costpulse.models.cost_record import CostRecord

logger = structlog.get_logger()


class AlertService:
    """Manage alerts and send notifications for budget thresholds."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_alerts(self) -> List[Dict[str, Any]]:
        """Evaluate all active alerts and trigger notifications.

        Returns:
            List of triggered alerts
        """
        result = await self.session.execute(
            select(Alert).where(Alert.is_active.is_(True))
        )
        alerts = result.scalars().all()

        triggered = []
        for alert in alerts:
            should_fire, current_value, message = await self._evaluate_alert(alert)
            if should_fire and await self._check_cooldown(alert):
                history = AlertHistory(
                    alert_id=alert.id,
                    status="triggered",
                    current_value=current_value,
                    message=message,
                    notification_sent={},
                )
                self.session.add(history)

                # Send notifications
                sent = await self._send_notifications(alert, current_value, message)
                history.notification_sent = sent

                triggered.append({
                    "alert_id": str(alert.id),
                    "alert_name": alert.name,
                    "alert_type": alert.alert_type,
                    "current_value": current_value,
                    "threshold": alert.threshold_value,
                    "message": message,
                    "notifications_sent": sent,
                })

        if triggered:
            await self.session.flush()
            logger.info("Alerts triggered", count=len(triggered))

        return triggered

    async def _evaluate_alert(self, alert: Alert) -> tuple:
        """Evaluate whether an alert condition is met.

        Returns:
            (should_fire, current_value, message)
        """
        if alert.alert_type == "budget_threshold":
            return await self._check_budget_threshold(alert)
        elif alert.alert_type == "cost_spike":
            return await self._check_cost_spike(alert)
        elif alert.alert_type == "daily_budget":
            return await self._check_daily_budget(alert)
        return False, 0.0, ""

    async def _check_budget_threshold(self, alert: Alert) -> tuple:
        """Check if monthly spend exceeds budget threshold."""
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        query = select(func.sum(CostRecord.cost_usd)).where(
            CostRecord.usage_date >= month_start
        )
        if alert.workspace_id:
            query = query.where(CostRecord.workspace_id == alert.workspace_id)

        result = await self.session.execute(query)
        current_spend = result.scalar() or 0.0

        if alert.threshold_type == "percentage":
            # Percentage of budget used
            budget = alert.threshold_value
            pct_used = (current_spend / budget * 100) if budget > 0 else 0
            conditions = alert.conditions or {}
            pct_threshold = conditions.get("percentage_threshold", 80)
            if pct_used >= pct_threshold:
                return (
                    True,
                    current_spend,
                    f"Monthly spend ${current_spend:,.2f} has reached {pct_used:.0f}% of ${budget:,.2f} budget",
                )
        else:
            if current_spend >= alert.threshold_value:
                return (
                    True,
                    current_spend,
                    f"Monthly spend ${current_spend:,.2f} exceeds threshold ${alert.threshold_value:,.2f}",
                )

        return False, current_spend, ""

    async def _check_cost_spike(self, alert: Alert) -> tuple:
        """Check for sudden cost increases."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)

        # Today's cost
        today_result = await self.session.execute(
            select(func.sum(CostRecord.cost_usd)).where(
                CostRecord.usage_date >= today_start
            )
        )
        today_cost = today_result.scalar() or 0.0

        # Yesterday's cost
        yesterday_result = await self.session.execute(
            select(func.sum(CostRecord.cost_usd)).where(
                CostRecord.usage_date >= yesterday_start,
                CostRecord.usage_date < today_start,
            )
        )
        yesterday_cost = yesterday_result.scalar() or 0.0

        if yesterday_cost > 0:
            pct_change = ((today_cost - yesterday_cost) / yesterday_cost) * 100
            threshold_pct = alert.threshold_value or 50.0
            if pct_change >= threshold_pct:
                return (
                    True,
                    today_cost,
                    f"Cost spike detected: ${today_cost:,.2f} today vs ${yesterday_cost:,.2f} yesterday ({pct_change:+.1f}%)",
                )

        return False, today_cost, ""

    async def _check_daily_budget(self, alert: Alert) -> tuple:
        """Check if daily spend exceeds threshold."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        result = await self.session.execute(
            select(func.sum(CostRecord.cost_usd)).where(
                CostRecord.usage_date >= today_start
            )
        )
        daily_cost = result.scalar() or 0.0

        if daily_cost >= alert.threshold_value:
            return (
                True,
                daily_cost,
                f"Daily spend ${daily_cost:,.2f} exceeds threshold ${alert.threshold_value:,.2f}",
            )

        return False, daily_cost, ""

    async def _check_cooldown(self, alert: Alert) -> bool:
        """Check if alert is in cooldown period."""
        result = await self.session.execute(
            select(AlertHistory)
            .where(
                AlertHistory.alert_id == alert.id,
                AlertHistory.triggered_at
                >= datetime.now(timezone.utc) - timedelta(minutes=alert.cooldown_minutes),
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is None

    async def _send_notifications(
        self, alert: Alert, current_value: float, message: str
    ) -> Dict[str, bool]:
        """Send alert notifications via configured channels."""
        sent = {}
        channels = alert.notification_channels or {}

        if channels.get("slack"):
            sent["slack"] = await self._send_slack(alert, message)

        if channels.get("email"):
            sent["email"] = await self._send_email(alert, message)

        return sent

    async def _send_slack(self, alert: Alert, message: str) -> bool:
        """Send Slack notification."""
        try:
            import os
            webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
            if not webhook_url:
                logger.warning("Slack webhook URL not configured")
                return False

            from slack_sdk.webhook import WebhookClient
            client = WebhookClient(webhook_url)
            response = client.send(
                text=f":rotating_light: *CostPulse Alert: {alert.name}*\n{message}",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f":rotating_light: *CostPulse Alert: {alert.name}*",
                        },
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": message},
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"Alert type: {alert.alert_type} | Team: {alert.team_id or 'All'}",
                            }
                        ],
                    },
                ],
            )
            return response.status_code == 200
        except Exception as e:
            logger.error("Failed to send Slack notification", error=str(e))
            return False

    async def _send_email(self, alert: Alert, message: str) -> bool:
        """Send email notification (placeholder for SMTP integration)."""
        logger.info("Email notification", alert=alert.name, message=message)
        return True

    # CRUD operations

    async def create_alert(self, data: Dict[str, Any]) -> Alert:
        """Create a new alert configuration."""
        alert = Alert(**data)
        self.session.add(alert)
        await self.session.flush()
        return alert

    async def update_alert(self, alert_id: uuid.UUID, data: Dict[str, Any]) -> Optional[Alert]:
        """Update an existing alert."""
        result = await self.session.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            return None
        for key, value in data.items():
            if hasattr(alert, key):
                setattr(alert, key, value)
        await self.session.flush()
        return alert

    async def delete_alert(self, alert_id: uuid.UUID) -> bool:
        """Delete an alert."""
        result = await self.session.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            return False
        await self.session.delete(alert)
        await self.session.flush()
        return True

    async def get_alert_history(
        self, alert_id: Optional[uuid.UUID] = None, limit: int = 50
    ) -> List[AlertHistory]:
        """Get alert firing history."""
        query = select(AlertHistory).order_by(AlertHistory.triggered_at.desc()).limit(limit)
        if alert_id:
            query = query.where(AlertHistory.alert_id == alert_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
