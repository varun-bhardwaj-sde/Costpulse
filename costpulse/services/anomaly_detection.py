"""ML-based cost anomaly detection service."""

from datetime import datetime, timedelta
from typing import Any, Dict, List

import numpy as np
import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from costpulse.core.constants import ANOMALY_THRESHOLDS
from costpulse.models.cost_record import CostRecord

logger = structlog.get_logger()


class AnomalyDetectionService:
    """Detect cost anomalies using statistical methods."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.spike_threshold = ANOMALY_THRESHOLDS["cost_spike_percent"]

    async def detect_anomalies(
        self,
        lookback_days: int = 30,
        sensitivity: float = 2.0,
    ) -> List[Dict[str, Any]]:
        """Detect cost anomalies across all dimensions.

        Uses Z-score and rolling average comparison.

        Args:
            lookback_days: Days of historical data to analyze
            sensitivity: Z-score threshold (lower = more sensitive)

        Returns:
            List of detected anomalies
        """
        anomalies = []

        # Detect daily cost spikes
        daily_anomalies = await self._detect_daily_spikes(lookback_days, sensitivity)
        anomalies.extend(daily_anomalies)

        # Detect per-workspace anomalies
        workspace_anomalies = await self._detect_workspace_spikes(lookback_days, sensitivity)
        anomalies.extend(workspace_anomalies)

        # Detect per-SKU anomalies
        sku_anomalies = await self._detect_sku_spikes(lookback_days, sensitivity)
        anomalies.extend(sku_anomalies)

        logger.info("Anomaly detection complete", anomalies_found=len(anomalies))
        return anomalies

    async def _detect_daily_spikes(
        self, lookback_days: int, sensitivity: float
    ) -> List[Dict[str, Any]]:
        """Detect days where total spend deviates significantly."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=lookback_days)

        result = await self.session.execute(
            select(
                func.date_trunc("day", CostRecord.usage_date).label("day"),
                func.sum(CostRecord.cost_usd).label("daily_cost"),
            )
            .where(CostRecord.usage_date >= start_date)
            .group_by(func.date_trunc("day", CostRecord.usage_date))
            .order_by(func.date_trunc("day", CostRecord.usage_date))
        )
        rows = result.all()

        if len(rows) < 7:
            return []

        costs = [float(row.daily_cost) for row in rows]
        dates = [row.day for row in rows]

        return self._find_zscore_anomalies(
            costs, dates, "daily_total", sensitivity
        )

    async def _detect_workspace_spikes(
        self, lookback_days: int, sensitivity: float
    ) -> List[Dict[str, Any]]:
        """Detect workspaces with unusual cost patterns."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=lookback_days)

        result = await self.session.execute(
            select(
                CostRecord.workspace_id,
                func.date_trunc("day", CostRecord.usage_date).label("day"),
                func.sum(CostRecord.cost_usd).label("daily_cost"),
            )
            .where(CostRecord.usage_date >= start_date)
            .group_by(CostRecord.workspace_id, func.date_trunc("day", CostRecord.usage_date))
            .order_by(CostRecord.workspace_id, func.date_trunc("day", CostRecord.usage_date))
        )
        rows = result.all()

        # Group by workspace
        workspace_data: Dict[str, List] = {}
        workspace_dates: Dict[str, List] = {}
        for row in rows:
            ws = row.workspace_id
            if ws not in workspace_data:
                workspace_data[ws] = []
                workspace_dates[ws] = []
            workspace_data[ws].append(float(row.daily_cost))
            workspace_dates[ws].append(row.day)

        anomalies = []
        for ws_id, costs in workspace_data.items():
            if len(costs) < 7:
                continue
            ws_anomalies = self._find_zscore_anomalies(
                costs, workspace_dates[ws_id], f"workspace:{ws_id}", sensitivity
            )
            anomalies.extend(ws_anomalies)

        return anomalies

    async def _detect_sku_spikes(
        self, lookback_days: int, sensitivity: float
    ) -> List[Dict[str, Any]]:
        """Detect SKUs with unusual cost patterns."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=lookback_days)

        result = await self.session.execute(
            select(
                CostRecord.sku_name,
                func.date_trunc("day", CostRecord.usage_date).label("day"),
                func.sum(CostRecord.cost_usd).label("daily_cost"),
            )
            .where(CostRecord.usage_date >= start_date)
            .group_by(CostRecord.sku_name, func.date_trunc("day", CostRecord.usage_date))
            .order_by(CostRecord.sku_name, func.date_trunc("day", CostRecord.usage_date))
        )
        rows = result.all()

        sku_data: Dict[str, List] = {}
        sku_dates: Dict[str, List] = {}
        for row in rows:
            sku = row.sku_name
            if sku not in sku_data:
                sku_data[sku] = []
                sku_dates[sku] = []
            sku_data[sku].append(float(row.daily_cost))
            sku_dates[sku].append(row.day)

        anomalies = []
        for sku, costs in sku_data.items():
            if len(costs) < 7:
                continue
            sku_anomalies = self._find_zscore_anomalies(
                costs, sku_dates[sku], f"sku:{sku}", sensitivity
            )
            anomalies.extend(sku_anomalies)

        return anomalies

    def _find_zscore_anomalies(
        self,
        values: List[float],
        dates: List,
        dimension: str,
        sensitivity: float,
    ) -> List[Dict[str, Any]]:
        """Find anomalies using Z-score method with rolling window."""
        anomalies = []
        arr = np.array(values)

        # Use rolling window of 7 days
        window = min(7, len(arr) - 1)

        for i in range(window, len(arr)):
            window_data = arr[max(0, i - window):i]
            mean = np.mean(window_data)
            std = np.std(window_data)

            if std == 0:
                continue

            z_score = (arr[i] - mean) / std
            pct_change = ((arr[i] - mean) / mean * 100) if mean > 0 else 0

            if abs(z_score) > sensitivity:
                anomalies.append({
                    "dimension": dimension,
                    "date": dates[i].isoformat() if hasattr(dates[i], "isoformat") else str(dates[i]),
                    "value": float(arr[i]),
                    "expected": float(mean),
                    "z_score": float(z_score),
                    "pct_change": float(pct_change),
                    "severity": "critical" if abs(z_score) > 3 else "high" if abs(z_score) > 2.5 else "medium",
                    "direction": "spike" if z_score > 0 else "drop",
                })

        return anomalies
