"""Collector for Databricks System Tables."""

from datetime import datetime
from typing import Any, Dict, List

import structlog

from costpulse.collectors.base import BaseCollector

logger = structlog.get_logger()


class SystemTablesCollector(BaseCollector):
    """Collector for Databricks System Tables."""

    async def collect(self) -> List[Dict[str, Any]]:
        """Fetch billing data from system.billing.usage.

        Returns:
            List of raw billing records from system tables
        """
        # Query last 24 hours by default
        query = """
        SELECT
            usage_date,
            workspace_id,
            sku_name,
            cloud,
            usage_unit,
            usage_quantity,
            custom_tags,
            usage_metadata
        FROM system.billing.usage
        WHERE usage_date >= current_date() - INTERVAL 1 DAY
        ORDER BY usage_date DESC
        """

        try:
            # Execute query using Databricks SQL
            result = self.client.statement_execution.execute_statement(
                warehouse_id=self._get_sql_warehouse_id(),
                statement=query,
                wait_timeout="30s",
            )

            if result.result and result.result.data_array:
                return [
                    dict(
                        zip(
                            [col.name for col in result.manifest.schema.columns],
                            row,
                        )
                    )
                    for row in result.result.data_array
                ]
            return []

        except Exception as e:
            logger.error("Failed to query system tables", error=str(e))
            raise

    def _get_sql_warehouse_id(self) -> str:
        """Get first available SQL warehouse.

        Returns:
            SQL warehouse ID

        Raises:
            ValueError: If no SQL warehouses are available
        """
        warehouses = list(self.client.warehouses.list())
        if not warehouses:
            raise ValueError("No SQL warehouses available")
        # Prefer serverless
        for wh in warehouses:
            if wh.warehouse_type and "SERVERLESS" in wh.warehouse_type.value:
                return wh.id
        return warehouses[0].id

    async def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform billing data to standardized format.

        Args:
            data: Raw billing records

        Returns:
            List of transformed cost records
        """
        from costpulse.core.constants import DBU_RATES

        transformed = []
        for row in data:
            sku = row.get("sku_name", "UNKNOWN")
            dbu_count = float(row.get("usage_quantity", 0))

            # Get DBU rate, warn if unknown SKU
            dbu_rate = DBU_RATES.get(sku)
            if dbu_rate is None:
                logger.warning(
                    "Unknown SKU using default rate",
                    sku=sku,
                    default_rate=0.15
                )
                dbu_rate = 0.15  # Default to STANDARD_JOBS_COMPUTE rate

            transformed.append(
                {
                    "timestamp": datetime.fromisoformat(str(row["usage_date"])),
                    "workspace_id": row.get("workspace_id"),
                    "sku_name": sku,
                    "cloud": row.get("cloud"),
                    "dbu_count": dbu_count,
                    "dbu_rate": dbu_rate,
                    "cost_usd": dbu_count * dbu_rate,
                    "tags": row.get("custom_tags", {}),
                    "metadata": row.get("usage_metadata", {}),
                }
            )

        return transformed
