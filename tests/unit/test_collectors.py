"""Tests for data collector transform logic (no Databricks SDK needed)."""

import sys
from unittest.mock import MagicMock

# Mock out the databricks SDK modules before any collector imports
_mock_sdk = MagicMock()
_mock_config = MagicMock()
sys.modules["databricks"] = _mock_sdk
sys.modules["databricks.sdk"] = _mock_sdk
sys.modules["databricks.sdk.config"] = _mock_config

from datetime import datetime, timezone  # noqa: E402

import pytest  # noqa: E402

from costpulse.collectors.cluster_collector import ClusterCollector  # noqa: E402
from costpulse.collectors.job_collector import JobCollector  # noqa: E402
from costpulse.collectors.user_collector import UserCollector  # noqa: E402
from costpulse.collectors.warehouse_collector import WarehouseCollector  # noqa: E402


class TestClusterCollectorTransform:
    @pytest.mark.asyncio
    async def test_transform_running_cluster(self):
        collector = ClusterCollector.__new__(ClusterCollector)
        raw_data = [
            {
                "cluster_id": "cl-123",
                "cluster_name": "prod-etl",
                "state": "RUNNING",
                "creator_user_name": "admin@company.com",
                "node_type_id": "i3.xlarge",
                "driver_node_type_id": "i3.xlarge",
                "num_workers": 4,
                "autoscale": {"min_workers": 2, "max_workers": 8},
                "spark_version": "14.3.x-scala2.12",
                "autotermination_minutes": 30,
                "custom_tags": {"team": "data-eng"},
                "cluster_source": "UI",
                "last_activity_time": None,
                "start_time": None,
                "runtime_engine": None,
            }
        ]

        result = await collector.transform(raw_data)
        assert len(result) == 1
        assert result[0]["cluster_id"] == "cl-123"
        assert result[0]["num_workers"] == 4
        assert result[0]["autoscale_min"] == 2
        assert result[0]["autoscale_max"] == 8

    @pytest.mark.asyncio
    async def test_transform_idle_detection(self):
        collector = ClusterCollector.__new__(ClusterCollector)
        old_time = datetime.now(timezone.utc).timestamp() * 1000 - (2 * 3600 * 1000)
        raw_data = [
            {
                "cluster_id": "cl-456",
                "cluster_name": "idle-cluster",
                "state": "RUNNING",
                "creator_user_name": "user@company.com",
                "node_type_id": "m5.xlarge",
                "driver_node_type_id": "m5.xlarge",
                "num_workers": 2,
                "autoscale": {"min_workers": None, "max_workers": None},
                "spark_version": "14.3.x",
                "autotermination_minutes": 0,
                "custom_tags": {},
                "cluster_source": "UI",
                "last_activity_time": old_time,
                "start_time": None,
                "runtime_engine": None,
            }
        ]

        result = await collector.transform(raw_data)
        assert result[0]["is_idle"] is True
        assert result[0]["idle_time_hours"] > 1.0

    @pytest.mark.asyncio
    async def test_transform_photon(self):
        collector = ClusterCollector.__new__(ClusterCollector)
        raw_data = [
            {
                "cluster_id": "cl-789",
                "cluster_name": "photon",
                "state": "TERMINATED",
                "creator_user_name": "admin@co.com",
                "node_type_id": "i3.xlarge",
                "driver_node_type_id": "i3.xlarge",
                "num_workers": 4,
                "autoscale": {"min_workers": None, "max_workers": None},
                "spark_version": "14.3.x-photon",
                "autotermination_minutes": 30,
                "custom_tags": {},
                "cluster_source": "UI",
                "last_activity_time": None,
                "start_time": None,
                "runtime_engine": "PHOTON",
            }
        ]

        result = await collector.transform(raw_data)
        assert result[0]["photon_enabled"] is True


class TestJobCollectorTransform:
    @pytest.mark.asyncio
    async def test_transform_job_run(self):
        collector = JobCollector.__new__(JobCollector)
        now = datetime.now(timezone.utc)
        start_ms = int(now.timestamp() * 1000) - 3600000
        end_ms = int(now.timestamp() * 1000)

        raw_data = [
            {
                "job_id": "100",
                "run_id": "200",
                "job_name": "daily-etl",
                "creator_user_name": "admin@co.com",
                "state": "TERMINATED",
                "result_state": "SUCCESS",
                "start_time": start_ms,
                "end_time": end_ms,
                "run_type": "JOB_RUN",
                "cluster_id": "cl-123",
                "tasks": [1, 2, 3],
                "schedule": "0 0 * * *",
                "tags": {"env": "prod"},
            }
        ]

        result = await collector.transform(raw_data)
        assert len(result) == 1
        assert result[0]["duration_seconds"] == pytest.approx(3600, abs=5)
        assert result[0]["cost_usd"] > 0
        assert result[0]["num_tasks"] == 3


class TestWarehouseCollectorTransform:
    @pytest.mark.asyncio
    async def test_serverless(self):
        collector = WarehouseCollector.__new__(WarehouseCollector)
        raw_data = [
            {
                "id": "wh-001",
                "name": "Serverless",
                "state": "RUNNING",
                "cluster_size": "Medium",
                "min_num_clusters": 1,
                "max_num_clusters": 4,
                "auto_stop_mins": 10,
                "warehouse_type": "TYPE_SERVERLESS",
                "spot_instance_policy": None,
                "enable_photon": True,
                "creator_name": "admin@co.com",
                "num_active_sessions": 5,
                "num_clusters": 2,
                "tags": {},
            }
        ]

        result = await collector.transform(raw_data)
        assert result[0]["is_serverless"] is True
        assert result[0]["is_idle"] is False

    @pytest.mark.asyncio
    async def test_idle(self):
        collector = WarehouseCollector.__new__(WarehouseCollector)
        raw_data = [
            {
                "id": "wh-002",
                "name": "Classic",
                "state": "RUNNING",
                "cluster_size": "Small",
                "min_num_clusters": 1,
                "max_num_clusters": 1,
                "auto_stop_mins": 0,
                "warehouse_type": "TYPE_CLASSIC",
                "spot_instance_policy": None,
                "enable_photon": False,
                "creator_name": "admin@co.com",
                "num_active_sessions": 0,
                "num_clusters": 1,
                "tags": {},
            }
        ]

        result = await collector.transform(raw_data)
        assert result[0]["is_idle"] is True


class TestUserCollectorTransform:
    @pytest.mark.asyncio
    async def test_team_discovery(self):
        collector = UserCollector.__new__(UserCollector)
        raw_data = [
            {
                "type": "user",
                "id": "u1",
                "user_name": "alice@co.com",
                "display_name": "Alice",
                "active": True,
                "groups": ["de"],
            },
            {
                "type": "user",
                "id": "u2",
                "user_name": "bob@co.com",
                "display_name": "Bob",
                "active": True,
                "groups": ["de"],
            },
            {
                "type": "group",
                "id": "g1",
                "display_name": "de",
                "members": [{"id": "u1", "display": "Alice"}, {"id": "u2", "display": "Bob"}],
            },
        ]

        result = await collector.transform(raw_data)
        de_team = next(t for t in result if t["team_name"] == "de")
        assert de_team["member_count"] == 2

    @pytest.mark.asyncio
    async def test_system_groups_excluded(self):
        collector = UserCollector.__new__(UserCollector)
        raw_data = [
            {"type": "group", "id": "g1", "display_name": "admins", "members": []},
            {"type": "group", "id": "g2", "display_name": "users", "members": []},
            {"type": "group", "id": "g3", "display_name": "my-team", "members": []},
        ]

        result = await collector.transform(raw_data)
        team_names = [t["team_name"] for t in result]
        assert "admins" not in team_names
        assert "my-team" in team_names
