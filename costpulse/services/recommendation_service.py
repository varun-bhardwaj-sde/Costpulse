"""Recommendation service for idle cluster detection and right-sizing."""

from typing import Any, Dict, List

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from costpulse.models.cluster import ClusterInfo
from costpulse.models.recommendation import Recommendation

logger = structlog.get_logger()


class RecommendationService:
    """Generate optimization recommendations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def generate_all_recommendations(self) -> List[Dict[str, Any]]:
        """Run all recommendation engines and persist results.

        Returns:
            List of new recommendations generated
        """
        recommendations = []

        idle = await self._detect_idle_clusters()
        recommendations.extend(idle)

        right_size = await self._detect_right_sizing_opportunities()
        recommendations.extend(right_size)

        auto_term = await self._check_auto_termination()
        recommendations.extend(auto_term)

        # Persist recommendations
        for rec_data in recommendations:
            rec = Recommendation(**rec_data)
            self.session.add(rec)

        await self.session.flush()
        logger.info("Recommendations generated", count=len(recommendations))
        return recommendations

    async def _detect_idle_clusters(self) -> List[Dict[str, Any]]:
        """Find clusters that are running but idle."""
        result = await self.session.execute(
            select(ClusterInfo).where(
                ClusterInfo.state == "RUNNING",
                ClusterInfo.is_idle.is_(True),
            )
        )
        idle_clusters = result.scalars().all()

        recommendations = []
        for cluster in idle_clusters:
            hourly_cost = self._estimate_hourly_cost(cluster)
            idle_hours = cluster.idle_time_hours or 0
            wasted_cost = hourly_cost * idle_hours

            recommendations.append(
                {
                    "recommendation_type": "idle_cluster",
                    "severity": "high" if idle_hours > 2 else "medium",
                    "title": f"Idle cluster: {cluster.cluster_name}",
                    "description": (
                        f"Cluster '{cluster.cluster_name}' has been idle "
                        f"for {idle_hours:.1f} hours. "
                        f"Estimated wasted cost: ${wasted_cost:.2f}. "
                        f"Consider terminating or reducing timeout."
                    ),
                    "workspace_id": cluster.workspace_id,
                    "resource_id": cluster.cluster_id,
                    "resource_type": "cluster",
                    "current_cost": wasted_cost,
                    "estimated_savings": wasted_cost * 0.8,
                    "details": {
                        "cluster_name": cluster.cluster_name,
                        "idle_hours": idle_hours,
                        "hourly_cost": hourly_cost,
                        "node_type": cluster.node_type,
                        "num_workers": cluster.num_workers,
                        "action": "terminate",
                    },
                    "status": "open",
                }
            )

        return recommendations

    async def _detect_right_sizing_opportunities(self) -> List[Dict[str, Any]]:
        """Find over-provisioned clusters based on utilization."""
        result = await self.session.execute(
            select(ClusterInfo).where(
                ClusterInfo.state.in_(["RUNNING", "TERMINATED"]),
                ClusterInfo.avg_cpu_utilization.isnot(None),
            )
        )
        clusters = result.scalars().all()

        recommendations = []
        for cluster in clusters:
            cpu_util = cluster.avg_cpu_utilization or 0
            mem_util = cluster.avg_memory_utilization or 0

            # Under-utilized: less than 30% CPU and memory
            if cpu_util < 30 and mem_util < 30 and cluster.num_workers > 1:
                suggested_workers = max(1, cluster.num_workers // 2)
                current_hourly = self._estimate_hourly_cost(cluster)
                estimated_hourly = (
                    current_hourly * (suggested_workers + 1) / (cluster.num_workers + 1)
                )
                monthly_savings = (current_hourly - estimated_hourly) * 24 * 30

                recommendations.append(
                    {
                        "recommendation_type": "right_sizing",
                        "severity": "medium",
                        "title": f"Right-size cluster: {cluster.cluster_name}",
                        "description": (
                            f"Cluster '{cluster.cluster_name}' is under-utilized "
                            f"(CPU: {cpu_util:.0f}%, Memory: {mem_util:.0f}%). "
                            f"Reduce from {cluster.num_workers} to {suggested_workers} workers "
                            f"to save ~${monthly_savings:.0f}/month."
                        ),
                        "workspace_id": cluster.workspace_id,
                        "resource_id": cluster.cluster_id,
                        "resource_type": "cluster",
                        "current_cost": current_hourly * 24 * 30,
                        "estimated_savings": monthly_savings,
                        "details": {
                            "cluster_name": cluster.cluster_name,
                            "current_workers": cluster.num_workers,
                            "suggested_workers": suggested_workers,
                            "avg_cpu": cpu_util,
                            "avg_memory": mem_util,
                            "node_type": cluster.node_type,
                            "action": "resize",
                        },
                        "status": "open",
                    }
                )

            # Over-provisioned autoscale
            if (
                cluster.autoscale_min is not None
                and cluster.autoscale_max is not None
                and cluster.autoscale_max > 10
                and cpu_util < 40
            ):
                suggested_max = max(cluster.autoscale_min, cluster.autoscale_max // 2)
                recommendations.append(
                    {
                        "recommendation_type": "right_sizing",
                        "severity": "low",
                        "title": f"Reduce autoscale max: {cluster.cluster_name}",
                        "description": (
                            f"Cluster '{cluster.cluster_name}' has autoscale max of "
                            f"{cluster.autoscale_max} but typically uses less. "
                            f"Consider reducing max to {suggested_max}."
                        ),
                        "workspace_id": cluster.workspace_id,
                        "resource_id": cluster.cluster_id,
                        "resource_type": "cluster",
                        "estimated_savings": 0,
                        "details": {
                            "current_max": cluster.autoscale_max,
                            "suggested_max": suggested_max,
                            "action": "adjust_autoscale",
                        },
                        "status": "open",
                    }
                )

        return recommendations

    async def _check_auto_termination(self) -> List[Dict[str, Any]]:
        """Find clusters without auto-termination or with long timeouts."""
        result = await self.session.execute(
            select(ClusterInfo).where(
                ClusterInfo.cluster_type == "all-purpose",
                ClusterInfo.state.in_(["RUNNING", "TERMINATED"]),
            )
        )
        clusters = result.scalars().all()

        recommendations = []
        for cluster in clusters:
            auto_term = cluster.auto_termination_minutes or 0

            if auto_term == 0:
                recommendations.append(
                    {
                        "recommendation_type": "policy_enforcement",
                        "severity": "high",
                        "title": f"No auto-termination: {cluster.cluster_name}",
                        "description": (
                            f"Cluster '{cluster.cluster_name}' has no auto-termination configured. "
                            f"This can lead to runaway costs if the cluster is left idle."
                        ),
                        "workspace_id": cluster.workspace_id,
                        "resource_id": cluster.cluster_id,
                        "resource_type": "cluster",
                        "estimated_savings": self._estimate_hourly_cost(cluster) * 8,
                        "details": {
                            "cluster_name": cluster.cluster_name,
                            "suggested_timeout": 30,
                            "action": "set_auto_termination",
                        },
                        "status": "open",
                    }
                )
            elif auto_term > 120:
                recommendations.append(
                    {
                        "recommendation_type": "policy_enforcement",
                        "severity": "low",
                        "title": f"Long auto-termination: {cluster.cluster_name}",
                        "description": (
                            f"Cluster '{cluster.cluster_name}' has a "
                            f"{auto_term}-minute auto-termination. "
                            f"Consider reducing to 30-60 minutes."
                        ),
                        "workspace_id": cluster.workspace_id,
                        "resource_id": cluster.cluster_id,
                        "resource_type": "cluster",
                        "details": {
                            "current_timeout": auto_term,
                            "suggested_timeout": 60,
                            "action": "reduce_auto_termination",
                        },
                        "status": "open",
                    }
                )

        return recommendations

    def _estimate_hourly_cost(self, cluster: ClusterInfo) -> float:
        """Estimate hourly cost of a cluster."""
        from costpulse.core.constants import DBU_RATES, VM_COSTS

        nodes = (cluster.num_workers or 0) + 1  # workers + driver
        dbu_per_node = 2.0 if cluster.photon_enabled else 1.0
        dbu_rate = DBU_RATES.get("ALL_PURPOSE_COMPUTE", 0.55)
        dbu_cost = nodes * dbu_per_node * dbu_rate

        vm_rate = VM_COSTS.get("AWS", {}).get(cluster.node_type or "", 0.3)
        vm_cost = nodes * vm_rate

        return dbu_cost + vm_cost

    async def list_recommendations(
        self,
        status: str = "open",
        recommendation_type: str = None,
        limit: int = 50,
    ) -> List[Recommendation]:
        """List recommendations with optional filters."""
        query = select(Recommendation).order_by(Recommendation.created_at.desc()).limit(limit)
        if status:
            query = query.where(Recommendation.status == status)
        if recommendation_type:
            query = query.where(Recommendation.recommendation_type == recommendation_type)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_recommendation_status(self, rec_id, status: str) -> Recommendation | None:
        """Update recommendation status (e.g., accepted, dismissed)."""
        result = await self.session.execute(
            select(Recommendation).where(Recommendation.id == rec_id)
        )
        rec = result.scalar_one_or_none()
        if rec:
            rec.status = status
            await self.session.flush()
        return rec
