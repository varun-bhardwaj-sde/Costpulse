"""Cost allocation engine: rule-based + tag-based team cost attribution."""

import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from costpulse.models.allocation import AllocationRule, CostAllocation
from costpulse.models.cost_record import CostRecord
from costpulse.models.team import Team, TeamMember

logger = structlog.get_logger()


class CostAllocationService:
    """Service for allocating costs to teams using rules and tags."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def allocate_costs(
        self, period_start: datetime, period_end: datetime
    ) -> List[Dict[str, Any]]:
        """Run the full allocation engine for a given period.

        1. Fetch all cost records in the period
        2. Apply allocation rules in priority order
        3. Fall back to tag-based matching
        4. Assign unmatched costs to "Unallocated"

        Returns:
            List of allocation summaries per team
        """
        # Fetch cost records
        result = await self.session.execute(
            select(CostRecord).where(
                CostRecord.usage_date >= period_start,
                CostRecord.usage_date < period_end,
            )
        )
        cost_records = result.scalars().all()

        if not cost_records:
            logger.info("No cost records found for allocation period")
            return []

        # Fetch active rules ordered by priority
        rules_result = await self.session.execute(
            select(AllocationRule)
            .where(AllocationRule.is_active.is_(True))
            .order_by(AllocationRule.priority)
        )
        rules = rules_result.scalars().all()

        # Fetch teams and members
        teams_result = await self.session.execute(select(Team))
        teams = {str(t.id): t for t in teams_result.scalars().all()}

        members_result = await self.session.execute(select(TeamMember))
        email_to_team: Dict[str, str] = {}
        for member in members_result.scalars().all():
            email_to_team[member.email.lower()] = str(member.team_id)

        # Allocate each cost record
        allocations: Dict[str, Dict[str, float]] = {}
        unallocated: List[CostRecord] = []

        for record in cost_records:
            team_id = self._match_record_to_team(record, rules, email_to_team, teams)
            if team_id:
                if team_id not in allocations:
                    allocations[team_id] = {
                        "total_cost": 0.0,
                        "dbu_cost": 0.0,
                        "compute_cost": 0.0,
                        "records": 0,
                        "by_sku": {},
                        "by_workspace": {},
                    }
                alloc = allocations[team_id]
                alloc["total_cost"] += record.cost_usd
                alloc["dbu_cost"] += record.dbu_count * record.dbu_rate
                alloc["records"] += 1

                sku = record.sku_name
                alloc["by_sku"][sku] = alloc["by_sku"].get(sku, 0.0) + record.cost_usd

                ws = record.workspace_id
                alloc["by_workspace"][ws] = alloc["by_workspace"].get(ws, 0.0) + record.cost_usd
            else:
                unallocated.append(record)

        # Persist allocations
        results = []
        for team_id, data in allocations.items():
            allocation = CostAllocation(
                team_id=uuid.UUID(team_id),
                period_start=period_start,
                period_end=period_end,
                total_cost=data["total_cost"],
                dbu_cost=data["dbu_cost"],
                compute_cost=data.get("compute_cost", 0.0),
                breakdown={
                    "by_sku": data["by_sku"],
                    "by_workspace": data["by_workspace"],
                    "record_count": data["records"],
                },
                allocation_method="rule_based",
            )
            self.session.add(allocation)

            team = teams.get(team_id)
            results.append(
                {
                    "team_id": team_id,
                    "team_name": team.name if team else "Unknown",
                    "total_cost": data["total_cost"],
                    "dbu_cost": data["dbu_cost"],
                    "record_count": data["records"],
                }
            )

        # Handle unallocated costs
        if unallocated:
            total_unallocated = sum(r.cost_usd for r in unallocated)
            results.append(
                {
                    "team_id": None,
                    "team_name": "Unallocated",
                    "total_cost": total_unallocated,
                    "dbu_cost": sum(r.dbu_count * r.dbu_rate for r in unallocated),
                    "record_count": len(unallocated),
                }
            )

        await self.session.flush()
        logger.info(
            "Cost allocation complete",
            teams_allocated=len(allocations),
            unallocated_records=len(unallocated),
        )
        return results

    def _match_record_to_team(
        self,
        record: CostRecord,
        rules: List[AllocationRule],
        email_to_team: Dict[str, str],
        teams: Dict[str, Team],
    ) -> Optional[str]:
        """Match a cost record to a team using rules and heuristics."""
        # 1. Try rule-based matching
        for rule in rules:
            if self._rule_matches(record, rule):
                return str(rule.team_id)

        # 2. Try user-email matching
        if record.user_email:
            team_id = email_to_team.get(record.user_email.lower())
            if team_id:
                return team_id

        # 3. Try tag-based matching
        if record.tags:
            for team_id, team in teams.items():
                if team.tag_patterns and self._tags_match(record.tags, team.tag_patterns):
                    return team_id

        return None

    def _rule_matches(self, record: CostRecord, rule: AllocationRule) -> bool:
        """Check if a cost record matches an allocation rule."""
        conditions = rule.conditions
        rule_type = rule.rule_type

        if rule_type == "tag_match":
            tag_key = conditions.get("tag_key", "")
            tag_value = conditions.get("tag_value", "")
            return record.tags.get(tag_key) == tag_value

        elif rule_type == "user_match":
            emails = [e.lower() for e in conditions.get("emails", [])]
            return record.user_email and record.user_email.lower() in emails

        elif rule_type == "workspace_match":
            workspace_ids = conditions.get("workspace_ids", [])
            return record.workspace_id in workspace_ids

        elif rule_type == "cluster_match":
            patterns = conditions.get("cluster_name_patterns", [])
            if record.cluster_name:
                return any(re.search(p, record.cluster_name) for p in patterns)
            return False

        elif rule_type == "sku_match":
            skus = conditions.get("sku_names", [])
            return record.sku_name in skus

        return False

    def _tags_match(self, record_tags: dict, team_patterns: dict) -> bool:
        """Check if record tags match team tag patterns."""
        for key, pattern in team_patterns.items():
            value = record_tags.get(key, "")
            if isinstance(pattern, str) and re.search(pattern, str(value)):
                return True
        return False

    async def get_team_costs(
        self,
        team_id: uuid.UUID,
        period_start: datetime,
        period_end: datetime,
    ) -> Optional[Dict[str, Any]]:
        """Get allocated costs for a specific team."""
        result = await self.session.execute(
            select(CostAllocation).where(
                CostAllocation.team_id == team_id,
                CostAllocation.period_start >= period_start,
                CostAllocation.period_end <= period_end,
            )
        )
        allocations = result.scalars().all()
        if not allocations:
            return None

        total = sum(a.total_cost for a in allocations)
        return {
            "team_id": str(team_id),
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "total_cost": total,
            "allocations": [
                {
                    "period_start": a.period_start.isoformat(),
                    "period_end": a.period_end.isoformat(),
                    "total_cost": a.total_cost,
                    "breakdown": a.breakdown,
                }
                for a in allocations
            ],
        }
