"""Tests for database models — verify model schema and table names."""

import pytest


class TestWorkspaceModel:
    def test_workspace_table_name(self):
        from costpulse.models.workspace import Workspace
        assert Workspace.__tablename__ == "workspaces"

    def test_workspace_columns(self):
        from costpulse.models.workspace import Workspace
        cols = {c.name for c in Workspace.__table__.columns}
        assert "workspace_id" in cols
        assert "name" in cols
        assert "host" in cols
        assert "cloud" in cols
        assert "status" in cols
        assert "num_users" in cols


class TestCostRecordModel:
    def test_cost_record_table_name(self):
        from costpulse.models.cost_record import CostRecord
        assert CostRecord.__tablename__ == "cost_records"

    def test_cost_record_columns(self):
        from costpulse.models.cost_record import CostRecord
        cols = {c.name for c in CostRecord.__table__.columns}
        assert "usage_date" in cols
        assert "workspace_id" in cols
        assert "sku_name" in cols
        assert "dbu_count" in cols
        assert "dbu_rate" in cols
        assert "cost_usd" in cols
        assert "cluster_id" in cols
        assert "job_id" in cols
        assert "user_email" in cols
        assert "tags" in cols

    def test_cost_record_indexes(self):
        from costpulse.models.cost_record import CostRecord
        index_names = {idx.name for idx in CostRecord.__table__.indexes}
        assert "ix_cost_records_date_workspace" in index_names
        assert "ix_cost_records_date_sku" in index_names


class TestTeamModel:
    def test_team_table(self):
        from costpulse.models.team import Team
        assert Team.__tablename__ == "teams"
        cols = {c.name for c in Team.__table__.columns}
        assert "name" in cols
        assert "department" in cols
        assert "cost_center" in cols
        assert "manager_email" in cols
        assert "tag_patterns" in cols

    def test_team_member_table(self):
        from costpulse.models.team import TeamMember
        assert TeamMember.__tablename__ == "team_members"
        cols = {c.name for c in TeamMember.__table__.columns}
        assert "team_id" in cols
        assert "email" in cols
        assert "role" in cols


class TestAllocationModels:
    def test_allocation_rule_table(self):
        from costpulse.models.allocation import AllocationRule
        assert AllocationRule.__tablename__ == "allocation_rules"
        cols = {c.name for c in AllocationRule.__table__.columns}
        assert "rule_type" in cols
        assert "conditions" in cols
        assert "priority" in cols

    def test_cost_allocation_table(self):
        from costpulse.models.allocation import CostAllocation
        assert CostAllocation.__tablename__ == "cost_allocations"
        cols = {c.name for c in CostAllocation.__table__.columns}
        assert "team_id" in cols
        assert "total_cost" in cols
        assert "dbu_cost" in cols


class TestAlertModel:
    def test_alert_table(self):
        from costpulse.models.alert import Alert
        assert Alert.__tablename__ == "alerts"
        cols = {c.name for c in Alert.__table__.columns}
        assert "alert_type" in cols
        assert "threshold_value" in cols
        assert "notification_channels" in cols
        assert "is_active" in cols

    def test_alert_history_table(self):
        from costpulse.models.alert import AlertHistory
        assert AlertHistory.__tablename__ == "alert_history"
        cols = {c.name for c in AlertHistory.__table__.columns}
        assert "alert_id" in cols
        assert "status" in cols
        assert "current_value" in cols


class TestClusterModel:
    def test_cluster_table(self):
        from costpulse.models.cluster import ClusterInfo
        assert ClusterInfo.__tablename__ == "clusters"
        cols = {c.name for c in ClusterInfo.__table__.columns}
        assert "cluster_id" in cols
        assert "cluster_name" in cols
        assert "state" in cols
        assert "num_workers" in cols
        assert "photon_enabled" in cols
        assert "is_idle" in cols
        assert "idle_time_hours" in cols
        assert "total_cost_usd" in cols


class TestJobRunModel:
    def test_job_run_table(self):
        from costpulse.models.job import JobRun
        assert JobRun.__tablename__ == "job_runs"
        cols = {c.name for c in JobRun.__table__.columns}
        assert "job_id" in cols
        assert "run_id" in cols
        assert "job_name" in cols
        assert "duration_seconds" in cols
        assert "dbu_consumed" in cols
        assert "cost_usd" in cols


class TestRecommendationModel:
    def test_recommendation_table(self):
        from costpulse.models.recommendation import Recommendation
        assert Recommendation.__tablename__ == "recommendations"
        cols = {c.name for c in Recommendation.__table__.columns}
        assert "recommendation_type" in cols
        assert "severity" in cols
        assert "estimated_savings" in cols
        assert "status" in cols


class TestReportModel:
    def test_report_table(self):
        from costpulse.models.report import Report
        assert Report.__tablename__ == "reports"
        cols = {c.name for c in Report.__table__.columns}
        assert "report_type" in cols
        assert "format" in cols
        assert "file_path" in cols
        assert "status" in cols


class TestForecastModel:
    def test_forecast_table(self):
        from costpulse.models.forecast import CostForecast
        assert CostForecast.__tablename__ == "cost_forecasts"
        cols = {c.name for c in CostForecast.__table__.columns}
        assert "forecast_date" in cols
        assert "predicted_cost" in cols
        assert "lower_bound" in cols
        assert "upper_bound" in cols
        assert "model_type" in cols


class TestAllModelsImportable:
    def test_all_models_import(self):
        from costpulse.models import (
            Base,
            Workspace,
            CostRecord,
            Team,
            TeamMember,
            AllocationRule,
            CostAllocation,
            Alert,
            AlertHistory,
            ClusterInfo,
            JobRun,
            Recommendation,
            Report,
            CostForecast,
        )
        assert len(Base.metadata.tables) >= 12
