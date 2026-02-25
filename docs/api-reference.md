# API Reference

CostPulse provides a REST API with 40+ endpoints across 11 modules. All endpoints are prefixed with `/api/v1/`.

**Base URL**: `http://localhost:8000/api/v1`

**Interactive Docs**: Visit `http://localhost:8000/docs` for Swagger UI.

## Authentication

Some endpoints require an API key. Pass it via the `X-API-Key` header:

```bash
curl -H "X-API-Key: your_secret_key" http://localhost:8000/api/v1/...
```

The key is configured via the `API_SECRET_KEY` environment variable.

---

## Health Check

### `GET /api/v1/health`

Check if the API is running.

```bash
curl http://localhost:8000/api/v1/health
```

**Response:**
```json
{"status": "healthy", "service": "costpulse"}
```

---

## Dashboard

High-level cost metrics and aggregations for the dashboard UI.

### `GET /dashboard/overview`

Get cost overview with period-over-period comparison.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | int | 30 | Period length (1-365) |

```bash
curl "http://localhost:8000/api/v1/dashboard/overview?days=30"
```

**Response:**
```json
{
  "period_days": 30,
  "total_cost": 45230.50,
  "total_dbu": 312500.0,
  "record_count": 8750,
  "cost_change_pct": 12.3,
  "prev_period_cost": 40267.80,
  "active_clusters": 15,
  "idle_clusters": 3,
  "open_recommendations": 7,
  "potential_savings": 4500.00
}
```

### `GET /dashboard/cost-trend`

Get time-series cost data for charts.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | int | 30 | Period length (1-365) |
| `granularity` | string | "daily" | `daily`, `weekly`, or `monthly` |

```bash
curl "http://localhost:8000/api/v1/dashboard/cost-trend?days=30&granularity=daily"
```

**Response:**
```json
{
  "granularity": "daily",
  "data": [
    {"period": "2026-01-01T00:00:00", "cost": 1250.50, "dbu": 8500.0},
    {"period": "2026-01-02T00:00:00", "cost": 1380.25, "dbu": 9200.0}
  ]
}
```

### `GET /dashboard/cost-by-workspace`

Cost breakdown by Databricks workspace.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | int | 30 | Period length (1-365) |

```bash
curl "http://localhost:8000/api/v1/dashboard/cost-by-workspace?days=30"
```

**Response:**
```json
{
  "data": [
    {"workspace_id": "ws-prod-001", "cost": 25000.00, "dbu": 175000.0, "records": 5000},
    {"workspace_id": "ws-dev-002", "cost": 8000.00, "dbu": 55000.0, "records": 2000}
  ]
}
```

### `GET /dashboard/cost-by-sku`

Cost breakdown by SKU type (Jobs Compute, All-Purpose, SQL, etc.).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | int | 30 | Period length (1-365) |

```bash
curl "http://localhost:8000/api/v1/dashboard/cost-by-sku?days=30"
```

### `GET /dashboard/cost-by-user`

Top users ranked by cost.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | int | 30 | Period length (1-365) |
| `limit` | int | 20 | Max results (1-100) |

```bash
curl "http://localhost:8000/api/v1/dashboard/cost-by-user?days=30&limit=10"
```

### `GET /dashboard/cost-by-job`

Top jobs ranked by cost.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | int | 30 | Period length (1-365) |
| `limit` | int | 20 | Max results (1-100) |

```bash
curl "http://localhost:8000/api/v1/dashboard/cost-by-job?days=30&limit=10"
```

---

## Costs

Query and explore individual cost records.

### `GET /costs/`

Query cost records with filters and pagination.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | string | null | ISO date filter (e.g., `2026-01-01`) |
| `end_date` | string | null | ISO date filter |
| `workspace_id` | string | null | Filter by workspace |
| `sku_name` | string | null | Filter by SKU type |
| `user_email` | string | null | Filter by user |
| `limit` | int | 100 | Page size (1-1000) |
| `offset` | int | 0 | Pagination offset |

```bash
curl "http://localhost:8000/api/v1/costs/?start_date=2026-01-01&sku_name=JOBS_COMPUTE&limit=10"
```

**Response:**
```json
{
  "total": 350,
  "limit": 10,
  "offset": 0,
  "data": [
    {
      "id": "uuid",
      "usage_date": "2026-01-15T00:00:00",
      "workspace_id": "ws-prod-001",
      "sku_name": "JOBS_COMPUTE",
      "cloud": "aws",
      "dbu_count": 125.5,
      "dbu_rate": 0.15,
      "cost_usd": 18.825,
      "cluster_id": "cl-123",
      "job_id": "job-456",
      "user_email": "alice@company.com",
      "tags": {"team": "data-eng", "environment": "prod"}
    }
  ]
}
```

### `GET /costs/summary`

Aggregated cost summary for a period.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | int | 30 | Period length (1-365) |
| `workspace_id` | string | null | Filter by workspace |

```bash
curl "http://localhost:8000/api/v1/costs/summary?days=30"
```

**Response:**
```json
{
  "period_days": 30,
  "total_cost": 45230.50,
  "total_dbu": 312500.0,
  "avg_daily_cost": 1507.68,
  "avg_cost_per_record": 5.17,
  "total_records": 8750,
  "earliest_date": "2026-01-01T00:00:00",
  "latest_date": "2026-01-30T00:00:00"
}
```

### `GET /costs/by-date`

Daily cost totals.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | int | 30 | Period length (1-365) |
| `workspace_id` | string | null | Filter by workspace |

---

## Workspaces

Manage registered Databricks workspaces.

### `GET /workspaces/`

List all registered workspaces.

```bash
curl http://localhost:8000/api/v1/workspaces/
```

### `POST /workspaces/`

Register a new workspace.

```bash
curl -X POST http://localhost:8000/api/v1/workspaces/ \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "ws-prod-001",
    "name": "Production Workspace",
    "host": "https://adb-123.azuredatabricks.net",
    "cloud": "azure",
    "region": "eastus",
    "plan": "premium"
  }'
```

**Response:**
```json
{"id": "uuid", "workspace_id": "ws-prod-001", "name": "Production Workspace"}
```

### `GET /workspaces/{workspace_id}`

Get workspace details.

### `PATCH /workspaces/{workspace_id}`

Update workspace fields.

```bash
curl -X PATCH "http://localhost:8000/api/v1/workspaces/ws-prod-001" \
  -H "Content-Type: application/json" \
  -d '{"status": "active", "plan": "enterprise"}'
```

### `DELETE /workspaces/{workspace_id}`

Remove a workspace registration.

---

## Teams

Manage teams for cost attribution and chargeback.

### `GET /teams/`

List all teams.

```bash
curl http://localhost:8000/api/v1/teams/
```

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Data Engineering",
      "department": "Engineering",
      "cost_center": "CC-100",
      "manager_email": "manager@company.com",
      "member_count": 8,
      "created_at": "2026-01-01T00:00:00"
    }
  ]
}
```

### `POST /teams/`

Create a new team.

```bash
curl -X POST http://localhost:8000/api/v1/teams/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Data Engineering",
    "department": "Engineering",
    "cost_center": "CC-100",
    "manager_email": "manager@company.com",
    "tag_patterns": {"team": "data-eng"}
  }'
```

### `GET /teams/{team_id}`

Get team details including all members.

### `PATCH /teams/{team_id}`

Update team details.

### `DELETE /teams/{team_id}`

Delete a team.

### `POST /teams/{team_id}/members`

Add a member to a team.

```bash
curl -X POST "http://localhost:8000/api/v1/teams/{team_id}/members" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@company.com",
    "display_name": "Alice Smith",
    "role": "lead"
  }'
```

### `DELETE /teams/{team_id}/members/{member_id}`

Remove a member from a team.

---

## Allocations

Cost allocation rules and execution.

### `POST /allocations/run`

Run cost allocation for a period. Applies all active rules to assign costs to teams.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `period_start` | string | Yes | ISO date (e.g., `2026-01-01`) |
| `period_end` | string | Yes | ISO date (e.g., `2026-01-31`) |

```bash
curl -X POST "http://localhost:8000/api/v1/allocations/run?period_start=2026-01-01&period_end=2026-01-31"
```

### `GET /allocations/`

List allocation results.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `team_id` | string | null | Filter by team |
| `period_start` | string | null | Filter from date |
| `limit` | int | 50 | Max results (1-200) |

### `GET /allocations/rules`

List all allocation rules (ordered by priority).

### `POST /allocations/rules`

Create an allocation rule.

**Rule types:**

| Type | Conditions | Description |
|------|-----------|-------------|
| `tag_match` | `{"tag_key": "team", "tag_value": "data-eng"}` | Match by resource tag |
| `user_match` | `{"emails": ["alice@co.com", "bob@co.com"]}` | Match by user email |
| `workspace_match` | `{"workspace_ids": ["ws-prod-001"]}` | Match by workspace |
| `cluster_match` | `{"cluster_name_patterns": ["ml-.*", "ai-.*"]}` | Match by cluster name pattern (regex) |
| `sku_match` | `{"sku_names": ["JOBS_COMPUTE"]}` | Match by SKU type |

```bash
curl -X POST http://localhost:8000/api/v1/allocations/rules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tag-based: data-eng team",
    "team_id": "team-uuid-here",
    "rule_type": "tag_match",
    "conditions": {"tag_key": "team", "tag_value": "data-eng"},
    "priority": 10
  }'
```

Rules with lower `priority` numbers are evaluated first.

### `DELETE /allocations/rules/{rule_id}`

Delete an allocation rule.

---

## Alerts

Budget thresholds and cost spike notifications.

### `GET /alerts/`

List alert configurations.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `is_active` | bool | null | Filter by active/inactive |

```bash
curl http://localhost:8000/api/v1/alerts/
```

### `POST /alerts/`

Create a new alert.

**Alert types:**

| Type | Description | Threshold meaning |
|------|-------------|-------------------|
| `budget_threshold` | Monthly budget exceeded | Budget in USD |
| `cost_spike` | Day-over-day cost increase | Percentage threshold (e.g., 50 = 50%) |
| `daily_budget` | Daily spend limit | Daily limit in USD |

```bash
# Monthly budget alert
curl -X POST http://localhost:8000/api/v1/alerts/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Monthly Budget $50K",
    "alert_type": "budget_threshold",
    "threshold_value": 50000,
    "threshold_type": "absolute",
    "notification_channels": {"slack": true, "email": true},
    "cooldown_minutes": 120
  }'

# Cost spike alert (triggers when daily cost is 50%+ above yesterday)
curl -X POST http://localhost:8000/api/v1/alerts/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cost Spike Detection",
    "alert_type": "cost_spike",
    "threshold_value": 50,
    "threshold_type": "percentage",
    "notification_channels": {"slack": true},
    "cooldown_minutes": 60
  }'

# Daily budget limit
curl -X POST http://localhost:8000/api/v1/alerts/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Limit $2K",
    "alert_type": "daily_budget",
    "threshold_value": 2000,
    "threshold_type": "absolute",
    "notification_channels": {"slack": true},
    "cooldown_minutes": 60
  }'
```

### `PATCH /alerts/{alert_id}`

Update an alert (change threshold, enable/disable, etc.).

```bash
curl -X PATCH "http://localhost:8000/api/v1/alerts/{alert_id}" \
  -H "Content-Type: application/json" \
  -d '{"threshold_value": 60000, "is_active": true}'
```

### `DELETE /alerts/{alert_id}`

Delete an alert.

### `POST /alerts/check`

Manually trigger alert evaluation. Normally this runs on a schedule.

```bash
curl -X POST http://localhost:8000/api/v1/alerts/check
```

**Response:**
```json
{
  "triggered": [
    {
      "alert_id": "uuid",
      "alert_name": "Monthly Budget $50K",
      "alert_type": "budget_threshold",
      "current_value": 52340.50,
      "threshold": 50000,
      "message": "Monthly spend $52,340.50 exceeds threshold $50,000.00",
      "notifications_sent": {"slack": true, "email": true}
    }
  ],
  "count": 1
}
```

### `GET /alerts/history`

Get alert firing history.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `alert_id` | string | null | Filter by specific alert |
| `limit` | int | 50 | Max results (1-200) |

---

## Reports

Generate and download cost reports.

### `POST /reports/generate`

Generate a report.

**Report types:** `showback`, `chargeback`, `executive`, `team`

**Formats:** `csv`, `excel`, `pdf`

```bash
curl -X POST http://localhost:8000/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "showback",
    "format": "excel",
    "period_start": "2026-01-01",
    "period_end": "2026-01-31"
  }'
```

**Response:**
```json
{
  "id": "uuid",
  "name": "showback_2026-01-01_2026-01-31",
  "status": "completed",
  "file_path": "/var/costpulse/reports/showback_2026-01-01.xlsx",
  "summary": {"total_cost": 45230.50, "workspaces": 3, "users": 25}
}
```

### `GET /reports/`

List generated reports.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `report_type` | string | null | Filter by type |
| `limit` | int | 20 | Max results (1-100) |

### `GET /reports/{report_id}`

Get report details and status.

### `GET /reports/{report_id}/download`

Download the report file. Returns the file with appropriate Content-Type based on format.

```bash
curl -o report.xlsx "http://localhost:8000/api/v1/reports/{report_id}/download"
```

---

## Recommendations

Cost optimization suggestions.

### `GET /recommendations/`

List recommendations.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | "open" | Filter: `open`, `accepted`, `dismissed`, `implemented` |
| `recommendation_type` | string | null | Filter by type |
| `limit` | int | 50 | Max results (1-200) |

```bash
curl "http://localhost:8000/api/v1/recommendations/?status=open"
```

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "type": "idle_cluster",
      "severity": "high",
      "title": "Terminate idle cluster 'dev-analytics'",
      "description": "Cluster has been idle for 4.5 hours with auto-termination disabled",
      "workspace_id": "ws-prod-001",
      "resource_id": "cl-456",
      "resource_type": "cluster",
      "current_cost": 12.50,
      "estimated_savings": 12.50,
      "details": {"idle_hours": 4.5, "node_type": "i3.xlarge", "num_workers": 4},
      "status": "open",
      "created_at": "2026-01-15T10:30:00"
    }
  ]
}
```

**Recommendation types:**
- `idle_cluster` -- Cluster running with no activity
- `rightsizing` -- Cluster under-utilizing CPU or memory (<30%)
- `auto_termination` -- Running cluster with no auto-termination configured

### `POST /recommendations/generate`

Trigger a scan of all clusters to generate new recommendations.

```bash
curl -X POST http://localhost:8000/api/v1/recommendations/generate
```

### `PATCH /recommendations/{rec_id}/status`

Update a recommendation's status.

```bash
curl -X PATCH "http://localhost:8000/api/v1/recommendations/{rec_id}/status" \
  -H "Content-Type: application/json" \
  -d '{"status": "accepted"}'
```

Valid statuses: `accepted`, `dismissed`, `implemented`

---

## Forecasts

ML-powered cost predictions.

### `POST /forecasts/generate`

Generate cost forecasts.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `horizon_days` | int | 30 | Forecast horizon (7-90 days) |
| `workspace_id` | string | null | Scope to workspace |
| `team_id` | string | null | Scope to team |
| `granularity` | string | "daily" | `daily`, `weekly`, or `monthly` |

```bash
curl -X POST "http://localhost:8000/api/v1/forecasts/generate?horizon_days=30"
```

**Response:**
```json
{
  "status": "completed",
  "horizon_days": 30,
  "data_points": 30,
  "data": [
    {
      "date": "2026-02-01",
      "predicted_cost": 1520.00,
      "lower_bound": 1200.00,
      "upper_bound": 1840.00,
      "model": "linear"
    }
  ]
}
```

The `model` field indicates which forecasting method was used:
- `prophet` -- Facebook Prophet (if available)
- `linear` -- Linear regression fallback

### `GET /forecasts/summary`

Get a high-level forecast summary.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `horizon_days` | int | 30 | Forecast horizon (7-90 days) |

---

## Clusters

Cluster fleet monitoring.

### `GET /clusters/`

List clusters with filters.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `workspace_id` | string | null | Filter by workspace |
| `state` | string | null | Filter by state (`RUNNING`, `TERMINATED`, etc.) |
| `is_idle` | bool | null | Filter idle clusters |
| `limit` | int | 50 | Max results (1-200) |

```bash
# List only idle running clusters
curl "http://localhost:8000/api/v1/clusters/?state=RUNNING&is_idle=true"
```

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "cluster_id": "cl-123",
      "cluster_name": "prod-etl",
      "workspace_id": "ws-prod-001",
      "creator_email": "admin@company.com",
      "cluster_type": "all-purpose",
      "state": "RUNNING",
      "node_type": "i3.xlarge",
      "num_workers": 4,
      "photon_enabled": false,
      "auto_termination_minutes": 30,
      "avg_cpu_utilization": 25.0,
      "avg_memory_utilization": 40.0,
      "total_cost_usd": 156.30,
      "total_runtime_hours": 24.5,
      "idle_time_hours": 3.2,
      "is_idle": true,
      "tags": {"team": "data-eng"}
    }
  ]
}
```

### `GET /clusters/summary`

Cluster fleet summary stats.

```bash
curl http://localhost:8000/api/v1/clusters/summary
```

**Response:**
```json
{
  "total_clusters": 25,
  "running": 12,
  "idle": 3,
  "total_cost": 4520.00,
  "total_idle_hours": 18.5
}
```

---

## Tags

Resource tagging compliance.

### `GET /tags/compliance`

Check tag compliance across all resources.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `workspace_id` | string | null | Scope to workspace |
| `required_tags` | string | null | Comma-separated tag keys (default: `team,environment,project,cost_center`) |

```bash
# Check with default required tags
curl http://localhost:8000/api/v1/tags/compliance

# Check with custom tags
curl "http://localhost:8000/api/v1/tags/compliance?required_tags=team,environment,owner"
```

**Response:**
```json
{
  "cluster_compliance": {
    "total": 25,
    "compliant": 18,
    "non_compliant": 7,
    "compliance_pct": 72.0,
    "violations": [
      {
        "cluster_id": "cl-456",
        "cluster_name": "dev-scratch",
        "missing_tags": ["team", "cost_center"]
      }
    ]
  },
  "cost_compliance": {
    "total": 8750,
    "compliant": 6200,
    "non_compliant": 2550,
    "compliance_pct": 70.9
  },
  "tag_coverage": {
    "team": 85.0,
    "environment": 78.0,
    "project": 65.0,
    "cost_center": 55.0
  },
  "recommendations": [
    "Critical: 7 clusters missing required tags (28% non-compliant)",
    "Add 'cost_center' tag - only 55% coverage"
  ]
}
```

---

## Error Responses

All errors follow a consistent format:

```json
{"detail": "Error description here"}
```

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad request (invalid parameters) |
| 401 | Unauthorized (missing or invalid API key) |
| 404 | Resource not found |
| 409 | Conflict (duplicate resource) |
| 422 | Validation error (invalid request body) |
| 500 | Internal server error |
