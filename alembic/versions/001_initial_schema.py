"""Initial schema for CostPulse FinOps Platform.

Revision ID: 001
Revises:
Create Date: 2026-02-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable TimescaleDB extension
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")

    # Workspaces
    op.create_table(
        "workspaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("host", sa.String(512), nullable=False),
        sa.Column("cloud", sa.String(50), nullable=False),
        sa.Column("region", sa.String(100)),
        sa.Column("status", sa.String(50), server_default="active"),
        sa.Column("plan", sa.String(50)),
        sa.Column("notes", sa.Text),
        sa.Column("num_users", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Cost Records (will be converted to hypertable)
    op.create_table(
        "cost_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("usage_date", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("workspace_id", sa.String(255), nullable=False, index=True),
        sa.Column("sku_name", sa.String(255), nullable=False, index=True),
        sa.Column("cloud", sa.String(50)),
        sa.Column("usage_unit", sa.String(50), server_default="DBU"),
        sa.Column("dbu_count", sa.Float, nullable=False, server_default="0"),
        sa.Column("dbu_rate", sa.Float, nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float, nullable=False, server_default="0"),
        sa.Column("cluster_id", sa.String(255), index=True),
        sa.Column("cluster_name", sa.String(255)),
        sa.Column("job_id", sa.String(255), index=True),
        sa.Column("job_name", sa.String(255)),
        sa.Column("warehouse_id", sa.String(255)),
        sa.Column("user_email", sa.String(255), index=True),
        sa.Column("tags", postgresql.JSONB, server_default="{}"),
        sa.Column("metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_cost_records_date_workspace", "cost_records", ["usage_date", "workspace_id"])
    op.create_index("ix_cost_records_date_sku", "cost_records", ["usage_date", "sku_name"])
    op.create_index("ix_cost_records_user_date", "cost_records", ["user_email", "usage_date"])

    # Convert cost_records to TimescaleDB hypertable
    op.execute(
        "SELECT create_hypertable('cost_records', 'usage_date', "
        "migrate_data => true, if_not_exists => true)"
    )

    # Teams
    op.create_table(
        "teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), unique=True, nullable=False),
        sa.Column("department", sa.String(255)),
        sa.Column("cost_center", sa.String(100)),
        sa.Column("manager_email", sa.String(255)),
        sa.Column("description", sa.Text),
        sa.Column("tag_patterns", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Team Members
    op.create_table(
        "team_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False, index=True),
        sa.Column("display_name", sa.String(255)),
        sa.Column("role", sa.String(100), server_default="member"),
        sa.Column("databricks_user_id", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Allocation Rules
    op.create_table(
        "allocation_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rule_type", sa.String(50), nullable=False),
        sa.Column("conditions", postgresql.JSONB, nullable=False),
        sa.Column("priority", sa.Integer, server_default="100"),
        sa.Column("description", sa.Text),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Cost Allocations
    op.create_table(
        "cost_allocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_cost", sa.Float, nullable=False, server_default="0"),
        sa.Column("dbu_cost", sa.Float, nullable=False, server_default="0"),
        sa.Column("compute_cost", sa.Float, nullable=False, server_default="0"),
        sa.Column("storage_cost", sa.Float, nullable=False, server_default="0"),
        sa.Column("breakdown", postgresql.JSONB, server_default="{}"),
        sa.Column("rule_id", postgresql.UUID(as_uuid=True)),
        sa.Column("allocation_method", sa.String(50), server_default="rule_based"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Alerts
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column(
            "team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="SET NULL"),
        ),
        sa.Column("workspace_id", sa.String(255)),
        sa.Column("threshold_value", sa.Float),
        sa.Column("threshold_type", sa.String(50), server_default="absolute"),
        sa.Column(
            "notification_channels",
            postgresql.JSONB,
            server_default='{"slack": true, "email": true}',
        ),
        sa.Column("conditions", postgresql.JSONB, server_default="{}"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("cooldown_minutes", sa.Integer, server_default="60"),
        sa.Column("description", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Alert History
    op.create_table(
        "alert_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "alert_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("alerts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("triggered_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(50), server_default="triggered"),
        sa.Column("current_value", sa.Float),
        sa.Column("message", sa.Text),
        sa.Column("notification_sent", postgresql.JSONB, server_default="{}"),
    )

    # Clusters
    op.create_table(
        "clusters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cluster_id", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("cluster_name", sa.String(255), nullable=False),
        sa.Column("workspace_id", sa.String(255), nullable=False, index=True),
        sa.Column("creator_email", sa.String(255), index=True),
        sa.Column("cluster_type", sa.String(50)),
        sa.Column("state", sa.String(50), server_default="UNKNOWN"),
        sa.Column("node_type", sa.String(100)),
        sa.Column("driver_node_type", sa.String(100)),
        sa.Column("num_workers", sa.Integer, server_default="0"),
        sa.Column("autoscale_min", sa.Integer),
        sa.Column("autoscale_max", sa.Integer),
        sa.Column("spark_version", sa.String(100)),
        sa.Column("photon_enabled", sa.Boolean, server_default="false"),
        sa.Column("auto_termination_minutes", sa.Integer),
        sa.Column("avg_cpu_utilization", sa.Float),
        sa.Column("avg_memory_utilization", sa.Float),
        sa.Column("total_dbu_consumed", sa.Float, server_default="0"),
        sa.Column("total_cost_usd", sa.Float, server_default="0"),
        sa.Column("total_runtime_hours", sa.Float, server_default="0"),
        sa.Column("idle_time_hours", sa.Float, server_default="0"),
        sa.Column("is_idle", sa.Boolean, server_default="false"),
        sa.Column("tags", postgresql.JSONB, server_default="{}"),
        sa.Column("last_active_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Job Runs
    op.create_table(
        "job_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", sa.String(255), nullable=False, index=True),
        sa.Column("run_id", sa.String(255), unique=True, nullable=False),
        sa.Column("job_name", sa.String(255)),
        sa.Column("workspace_id", sa.String(255), nullable=False, index=True),
        sa.Column("creator_email", sa.String(255), index=True),
        sa.Column("cluster_id", sa.String(255)),
        sa.Column("run_type", sa.String(50)),
        sa.Column("state", sa.String(50)),
        sa.Column("result_state", sa.String(50)),
        sa.Column("start_time", sa.DateTime(timezone=True)),
        sa.Column("end_time", sa.DateTime(timezone=True)),
        sa.Column("duration_seconds", sa.Integer, server_default="0"),
        sa.Column("dbu_consumed", sa.Float, server_default="0"),
        sa.Column("cost_usd", sa.Float, server_default="0"),
        sa.Column("num_tasks", sa.Integer, server_default="1"),
        sa.Column("tags", postgresql.JSONB, server_default="{}"),
        sa.Column("schedule", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Recommendations
    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("recommendation_type", sa.String(50), nullable=False, index=True),
        sa.Column("severity", sa.String(20), server_default="medium"),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("workspace_id", sa.String(255), index=True),
        sa.Column("resource_id", sa.String(255)),
        sa.Column("resource_type", sa.String(50)),
        sa.Column("current_cost", sa.Float),
        sa.Column("estimated_savings", sa.Float),
        sa.Column("details", postgresql.JSONB, server_default="{}"),
        sa.Column("status", sa.String(50), server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Reports
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("format", sa.String(20), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("file_path", sa.Text),
        sa.Column("file_size_bytes", sa.Integer, server_default="0"),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("parameters", postgresql.JSONB, server_default="{}"),
        sa.Column("summary", postgresql.JSONB, server_default="{}"),
        sa.Column("generated_by", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )

    # Cost Forecasts
    op.create_table(
        "cost_forecasts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", sa.String(255), index=True),
        sa.Column("team_id", sa.String(255), index=True),
        sa.Column("forecast_date", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("predicted_cost", sa.Float, nullable=False),
        sa.Column("lower_bound", sa.Float),
        sa.Column("upper_bound", sa.Float),
        sa.Column("confidence_level", sa.Float, server_default="0.95"),
        sa.Column("model_type", sa.String(50), server_default="prophet"),
        sa.Column("granularity", sa.String(20), server_default="daily"),
        sa.Column("model_metrics", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("cost_forecasts")
    op.drop_table("reports")
    op.drop_table("recommendations")
    op.drop_table("job_runs")
    op.drop_table("clusters")
    op.drop_table("alert_history")
    op.drop_table("alerts")
    op.drop_table("cost_allocations")
    op.drop_table("allocation_rules")
    op.drop_table("team_members")
    op.drop_table("teams")
    op.drop_table("cost_records")
    op.drop_table("workspaces")
