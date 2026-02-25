"""Collector for Databricks workspace users and groups for auto-discovery."""

from typing import Any, Dict, List

import structlog

from costpulse.collectors.base import BaseCollector

logger = structlog.get_logger()


class UserCollector(BaseCollector):
    """Collect users and groups from Databricks workspace for team auto-discovery."""

    async def collect(self) -> List[Dict[str, Any]]:
        """Fetch users and group memberships from the workspace.

        Returns:
            List of raw user/group records
        """
        try:
            users_data = []

            # Collect users
            users = list(self.client.users.list())
            for user in users:
                groups = []
                if user.groups:
                    groups = [g.display for g in user.groups if g.display]

                users_data.append(
                    {
                        "type": "user",
                        "id": user.id,
                        "user_name": user.user_name,
                        "display_name": user.display_name or user.user_name,
                        "active": user.active if hasattr(user, "active") else True,
                        "groups": groups,
                    }
                )

            # Collect groups
            try:
                groups = list(self.client.groups.list())
                for group in groups:
                    members = []
                    if group.members:
                        members = [
                            {"id": m.value, "display": m.display} for m in group.members if m.value
                        ]

                    users_data.append(
                        {
                            "type": "group",
                            "id": group.id,
                            "display_name": group.display_name,
                            "members": members,
                        }
                    )
            except Exception as e:
                logger.warning("Could not collect groups", error=str(e))

            logger.info(
                "Collected users and groups",
                users=sum(1 for u in users_data if u["type"] == "user"),
                groups=sum(1 for u in users_data if u["type"] == "group"),
            )
            return users_data
        except Exception as e:
            logger.error("Failed to collect users", error=str(e))
            raise

    async def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform user data into team-ready format.

        Auto-discovers teams from Databricks groups.

        Args:
            data: Raw user/group records

        Returns:
            List of discovered teams with members
        """
        # Build group -> members mapping
        groups_map: Dict[str, List[Dict[str, str]]] = {}
        users_map: Dict[str, Dict[str, Any]] = {}

        for record in data:
            if record["type"] == "user" and record.get("id"):
                users_map[record["id"]] = {
                    "email": record["user_name"],
                    "display_name": record["display_name"],
                    "databricks_user_id": record["id"],
                    "groups": record.get("groups", []),
                }
            elif record["type"] == "group" and record.get("display_name"):
                groups_map[record["display_name"]] = record.get("members", [])

        # Build teams from groups
        teams = []
        for group_name, members in groups_map.items():
            # Skip system groups
            if group_name in ("admins", "users", "account users"):
                continue

            team_members = []
            for member in members:
                user = users_map.get(member.get("id", ""))
                if user:
                    team_members.append(
                        {
                            "email": user["email"],
                            "display_name": user["display_name"],
                            "databricks_user_id": user["databricks_user_id"],
                        }
                    )

            teams.append(
                {
                    "team_name": group_name,
                    "members": team_members,
                    "member_count": len(team_members),
                    "source": "databricks_group",
                }
            )

        # Also include ungrouped users
        grouped_user_ids = set()
        for members in groups_map.values():
            for m in members:
                grouped_user_ids.add(m.get("id", ""))

        ungrouped = [
            {
                "email": u["email"],
                "display_name": u["display_name"],
                "databricks_user_id": u["databricks_user_id"],
            }
            for uid, u in users_map.items()
            if uid not in grouped_user_ids
        ]

        if ungrouped:
            teams.append(
                {
                    "team_name": "Unassigned",
                    "members": ungrouped,
                    "member_count": len(ungrouped),
                    "source": "auto_discovery",
                }
            )

        return teams
