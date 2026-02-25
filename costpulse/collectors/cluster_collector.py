"""Collector for Databricks cluster metadata and utilization."""

from datetime import datetime, timezone
from typing import Any, Dict, List

import structlog

from costpulse.collectors.base import BaseCollector

logger = structlog.get_logger()


class ClusterCollector(BaseCollector):
    """Collect cluster information from Databricks workspace."""

    async def collect(self) -> List[Dict[str, Any]]:
        """Fetch all clusters from the workspace.

        Returns:
            List of raw cluster records
        """
        try:
            clusters = list(self.client.clusters.list())
            raw_data = []
            for cluster in clusters:
                raw_data.append(
                    {
                        "cluster_id": cluster.cluster_id,
                        "cluster_name": cluster.cluster_name or "unnamed",
                        "state": cluster.state.value if cluster.state else "UNKNOWN",
                        "creator_user_name": cluster.creator_user_name,
                        "node_type_id": cluster.node_type_id,
                        "driver_node_type_id": cluster.driver_node_type_id or cluster.node_type_id,
                        "num_workers": cluster.num_workers or 0,
                        "autoscale": {
                            "min_workers": (
                                cluster.autoscale.min_workers if cluster.autoscale else None
                            ),
                            "max_workers": (
                                cluster.autoscale.max_workers if cluster.autoscale else None
                            ),
                        },
                        "spark_version": cluster.spark_version,
                        "autotermination_minutes": cluster.autotermination_minutes or 0,
                        "custom_tags": cluster.custom_tags or {},
                        "cluster_source": (
                            cluster.cluster_source.value if cluster.cluster_source else None
                        ),
                        "last_activity_time": cluster.last_activity_time,
                        "start_time": cluster.start_time,
                        "runtime_engine": getattr(cluster, "runtime_engine", None),
                    }
                )
            logger.info("Collected clusters", count=len(raw_data))
            return raw_data
        except Exception as e:
            logger.error("Failed to collect clusters", error=str(e))
            raise

    async def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform cluster data into standardized format.

        Args:
            data: Raw cluster records

        Returns:
            List of transformed cluster records
        """
        now = datetime.now(timezone.utc)
        transformed = []

        for cluster in data:
            last_activity = cluster.get("last_activity_time")
            idle_minutes = 0
            is_idle = False

            if last_activity and cluster["state"] == "RUNNING":
                if isinstance(last_activity, (int, float)):
                    last_dt = datetime.fromtimestamp(last_activity / 1000, tz=timezone.utc)
                else:
                    last_dt = last_activity
                idle_minutes = (now - last_dt).total_seconds() / 60
                is_idle = idle_minutes > 30

            photon_enabled = False
            runtime = cluster.get("runtime_engine")
            if runtime and str(runtime).upper() == "PHOTON":
                photon_enabled = True

            cluster_type = "all-purpose"
            source = cluster.get("cluster_source")
            if source and "JOB" in str(source).upper():
                cluster_type = "job"

            autoscale = cluster.get("autoscale", {})
            transformed.append(
                {
                    "cluster_id": cluster["cluster_id"],
                    "cluster_name": cluster["cluster_name"],
                    "creator_email": cluster.get("creator_user_name"),
                    "cluster_type": cluster_type,
                    "state": cluster["state"],
                    "node_type": cluster.get("node_type_id"),
                    "driver_node_type": cluster.get("driver_node_type_id"),
                    "num_workers": cluster.get("num_workers", 0),
                    "autoscale_min": autoscale.get("min_workers"),
                    "autoscale_max": autoscale.get("max_workers"),
                    "spark_version": cluster.get("spark_version"),
                    "photon_enabled": photon_enabled,
                    "auto_termination_minutes": cluster.get("autotermination_minutes", 0),
                    "idle_time_hours": idle_minutes / 60,
                    "is_idle": is_idle,
                    "tags": cluster.get("custom_tags", {}),
                    "last_active_at": last_activity,
                }
            )

        return transformed
