"""Tag compliance checker for Databricks resource governance."""

from typing import Any, Dict, List, Optional

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from costpulse.models.cluster import ClusterInfo
from costpulse.models.cost_record import CostRecord

logger = structlog.get_logger()

# Standard tags that should be present on all resources
DEFAULT_REQUIRED_TAGS = ["team", "environment", "project", "cost_center"]


class TagComplianceService:
    """Check and report on tag compliance across Databricks resources."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_compliance(
        self,
        required_tags: Optional[List[str]] = None,
        workspace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run a full tag compliance check.

        Args:
            required_tags: List of required tag keys
            workspace_id: Optional workspace filter

        Returns:
            Compliance report with overall score and violations
        """
        tags_to_check = required_tags or DEFAULT_REQUIRED_TAGS

        # Check clusters
        cluster_compliance = await self._check_cluster_tags(tags_to_check, workspace_id)

        # Check cost records for untagged usage
        cost_compliance = await self._check_cost_record_tags(tags_to_check, workspace_id)

        total_resources = cluster_compliance["total"] + cost_compliance["total"]
        total_compliant = cluster_compliance["compliant"] + cost_compliance["compliant"]
        compliance_pct = (total_compliant / total_resources * 100) if total_resources > 0 else 0

        report = {
            "overall_compliance_pct": round(compliance_pct, 1),
            "total_resources": total_resources,
            "compliant_resources": total_compliant,
            "non_compliant_resources": total_resources - total_compliant,
            "required_tags": tags_to_check,
            "clusters": cluster_compliance,
            "cost_records": cost_compliance,
            "tag_coverage": await self._get_tag_coverage(tags_to_check, workspace_id),
            "recommendations": self._generate_tag_recommendations(
                cluster_compliance, cost_compliance, tags_to_check
            ),
        }

        logger.info(
            "Tag compliance check complete",
            compliance_pct=compliance_pct,
            total=total_resources,
        )
        return report

    async def _check_cluster_tags(
        self, required_tags: List[str], workspace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check tag compliance on clusters."""
        query = select(ClusterInfo)
        if workspace_id:
            query = query.where(ClusterInfo.workspace_id == workspace_id)

        result = await self.session.execute(query)
        clusters = result.scalars().all()

        compliant = 0
        violations = []

        for cluster in clusters:
            tags = cluster.tags or {}
            missing = [t for t in required_tags if t not in tags]

            if not missing:
                compliant += 1
            else:
                violations.append({
                    "resource_type": "cluster",
                    "resource_id": cluster.cluster_id,
                    "resource_name": cluster.cluster_name,
                    "workspace_id": cluster.workspace_id,
                    "missing_tags": missing,
                    "existing_tags": list(tags.keys()),
                })

        return {
            "total": len(clusters),
            "compliant": compliant,
            "non_compliant": len(violations),
            "compliance_pct": round((compliant / len(clusters) * 100) if clusters else 0, 1),
            "violations": violations[:50],  # Limit to 50 violations
        }

    async def _check_cost_record_tags(
        self, required_tags: List[str], workspace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check tag compliance on cost records (unique cluster/job combinations)."""
        query = (
            select(
                CostRecord.cluster_id,
                CostRecord.cluster_name,
                CostRecord.workspace_id,
                CostRecord.tags,
            )
            .where(CostRecord.cluster_id.isnot(None))
            .distinct(CostRecord.cluster_id)
        )
        if workspace_id:
            query = query.where(CostRecord.workspace_id == workspace_id)

        result = await self.session.execute(query)
        records = result.all()

        compliant = 0
        violations = []

        for record in records:
            tags = record.tags or {}
            missing = [t for t in required_tags if t not in tags]

            if not missing:
                compliant += 1
            else:
                violations.append({
                    "resource_type": "cost_record",
                    "resource_id": record.cluster_id,
                    "resource_name": record.cluster_name or "unknown",
                    "workspace_id": record.workspace_id,
                    "missing_tags": missing,
                    "existing_tags": list(tags.keys()),
                })

        return {
            "total": len(records),
            "compliant": compliant,
            "non_compliant": len(violations),
            "compliance_pct": round((compliant / len(records) * 100) if records else 0, 1),
            "violations": violations[:50],
        }

    async def _get_tag_coverage(
        self, required_tags: List[str], workspace_id: Optional[str] = None
    ) -> Dict[str, float]:
        """Get per-tag coverage percentages."""
        query = select(CostRecord.tags).where(CostRecord.tags.isnot(None))
        if workspace_id:
            query = query.where(CostRecord.workspace_id == workspace_id)

        result = await self.session.execute(query)
        all_tags = [r.tags for r in result.all() if r.tags]

        if not all_tags:
            return {tag: 0.0 for tag in required_tags}

        total = len(all_tags)
        coverage = {}
        for tag in required_tags:
            count = sum(1 for tags in all_tags if tag in tags)
            coverage[tag] = round(count / total * 100, 1)

        return coverage

    def _generate_tag_recommendations(
        self,
        cluster_compliance: Dict,
        cost_compliance: Dict,
        required_tags: List[str],
    ) -> List[str]:
        """Generate actionable recommendations for improving tag compliance."""
        recs = []

        cluster_pct = cluster_compliance.get("compliance_pct", 0)
        if cluster_pct < 50:
            recs.append(
                f"Critical: Only {cluster_pct}% of clusters are properly tagged. "
                f"Enforce cluster policies to require tags: {', '.join(required_tags)}"
            )
        elif cluster_pct < 80:
            recs.append(
                f"Moderate: {cluster_pct}% of clusters are tagged. "
                f"Consider enabling tag enforcement in workspace admin settings."
            )

        # Find most commonly missing tags
        all_violations = cluster_compliance.get("violations", []) + cost_compliance.get("violations", [])
        missing_counts: Dict[str, int] = {}
        for v in all_violations:
            for tag in v.get("missing_tags", []):
                missing_counts[tag] = missing_counts.get(tag, 0) + 1

        if missing_counts:
            worst_tag = max(missing_counts, key=missing_counts.get)
            recs.append(
                f"Most commonly missing tag: '{worst_tag}' "
                f"(missing from {missing_counts[worst_tag]} resources)"
            )

        if not recs:
            recs.append("Tag compliance is good! All resources are properly tagged.")

        return recs
