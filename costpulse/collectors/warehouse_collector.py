"""Collector for Databricks SQL warehouse data."""

from typing import Any, Dict, List

import structlog

from costpulse.collectors.base import BaseCollector

logger = structlog.get_logger()


class WarehouseCollector(BaseCollector):
    """Collect SQL warehouse information from Databricks workspace."""

    async def collect(self) -> List[Dict[str, Any]]:
        """Fetch all SQL warehouses from the workspace.

        Returns:
            List of raw warehouse records
        """
        try:
            warehouses = list(self.client.warehouses.list())
            raw_data = []

            for wh in warehouses:
                raw_data.append(
                    {
                        "id": wh.id,
                        "name": wh.name,
                        "state": wh.state.value if wh.state else "UNKNOWN",
                        "cluster_size": wh.cluster_size,
                        "min_num_clusters": wh.min_num_clusters or 1,
                        "max_num_clusters": wh.max_num_clusters or 1,
                        "auto_stop_mins": wh.auto_stop_mins or 0,
                        "warehouse_type": (
                            wh.warehouse_type.value if wh.warehouse_type else "CLASSIC"
                        ),
                        "spot_instance_policy": (
                            wh.spot_instance_policy.value if wh.spot_instance_policy else None
                        ),
                        "enable_photon": (
                            wh.enable_photon if hasattr(wh, "enable_photon") else False
                        ),
                        "creator_name": wh.creator_name if hasattr(wh, "creator_name") else None,
                        "num_active_sessions": (
                            wh.num_active_sessions if hasattr(wh, "num_active_sessions") else 0
                        ),
                        "num_clusters": wh.num_clusters if hasattr(wh, "num_clusters") else 0,
                        "tags": self._extract_tags(wh),
                    }
                )

            logger.info("Collected warehouses", count=len(raw_data))
            return raw_data
        except Exception as e:
            logger.error("Failed to collect warehouses", error=str(e))
            raise

    @staticmethod
    def _extract_tags(wh) -> Dict[str, str]:
        """Extract custom tags from a warehouse object."""
        try:
            if hasattr(wh, "tags") and wh.tags:
                custom = getattr(wh.tags, "custom_tags", None)
                if custom:
                    return {t.key: t.value for t in custom}
        except Exception:
            pass
        return {}

    async def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform warehouse data into standardized format.

        Args:
            data: Raw warehouse records

        Returns:
            List of transformed warehouse records
        """
        transformed = []

        for wh in data:
            is_serverless = "SERVERLESS" in str(wh.get("warehouse_type", "")).upper()
            is_idle = wh.get("state") == "RUNNING" and wh.get("num_active_sessions", 0) == 0

            transformed.append(
                {
                    "warehouse_id": wh["id"],
                    "name": wh["name"],
                    "state": wh["state"],
                    "cluster_size": wh.get("cluster_size"),
                    "min_num_clusters": wh.get("min_num_clusters", 1),
                    "max_num_clusters": wh.get("max_num_clusters", 1),
                    "auto_stop_mins": wh.get("auto_stop_mins", 0),
                    "warehouse_type": wh.get("warehouse_type", "CLASSIC"),
                    "is_serverless": is_serverless,
                    "photon_enabled": wh.get("enable_photon", False),
                    "creator": wh.get("creator_name"),
                    "num_active_sessions": wh.get("num_active_sessions", 0),
                    "is_idle": is_idle,
                    "tags": wh.get("tags", {}),
                }
            )

        return transformed
