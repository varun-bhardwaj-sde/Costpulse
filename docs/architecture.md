# Architecture Guide

This document describes the CostPulse system design, data flow, and key components.

## System Overview

CostPulse follows a layered architecture:

```
┌──────────────────────────────────────────────────────────────┐
│                     Presentation Layer                        │
│  ┌────────────────────┐  ┌───────────────┐  ┌────────────┐  │
│  │  React Dashboard   │  │  REST API     │  │    CLI      │  │
│  │  (port 3000)       │  │  (port 8000)  │  │    Tool     │  │
│  └────────────────────┘  └───────────────┘  └────────────┘  │
├──────────────────────────────────────────────────────────────┤
│                      Service Layer                            │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │  Allocation  │  │  Anomaly     │  │  Recommendation    │  │
│  │  Engine      │  │  Detection   │  │  Engine            │  │
│  ├─────────────┤  ├──────────────┤  ├────────────────────┤  │
│  │  Alert       │  │  Forecast    │  │  Tag Compliance    │  │
│  │  Service     │  │  Service     │  │  Service           │  │
│  ├─────────────┤  ├──────────────┤  ├────────────────────┤  │
│  │  Report      │  │              │  │                    │  │
│  │  Service     │  │              │  │                    │  │
│  └─────────────┘  └──────────────┘  └────────────────────┘  │
├──────────────────────────────────────────────────────────────┤
│                    Data Collection Layer                       │
│  ┌──────────────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │  System Tables    │  │  Cluster │  │  Warehouse       │   │
│  │  Collector        │  │  Collect.│  │  Collector        │   │
│  ├──────────────────┤  ├──────────┤  ├──────────────────┤   │
│  │  Job Collector    │  │  User    │  │  Scheduler       │   │
│  │                   │  │  Collect.│  │  (background)    │   │
│  └──────────────────┘  └──────────┘  └──────────────────┘   │
├──────────────────────────────────────────────────────────────┤
│                      Storage Layer                            │
│  ┌───────────────────────────┐  ┌────────────────────────┐  │
│  │  TimescaleDB              │  │  Redis                 │  │
│  │  (PostgreSQL + Hypertable)│  │  (Cache + Pub/Sub)     │  │
│  └───────────────────────────┘  └────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## Data Flow

### Collection Pipeline

```
Databricks APIs ──> Collectors ──> Transform ──> TimescaleDB
                                                     │
                                          ┌──────────┴──────────┐
                                          │                     │
                                     Services              Scheduler
                                     (on-demand)       (periodic analysis)
                                          │                     │
                                          ▼                     ▼
                                      API/CLI              Alerts/Recs
```

1. **Collectors** fetch raw data from Databricks (billing, clusters, jobs, warehouses, users)
2. Each collector has a **transform** step that normalizes the data
3. Transformed data is stored in **TimescaleDB**
4. **Services** query the database to produce insights (anomalies, recommendations, forecasts)
5. The **Scheduler** runs collection and analysis on a configurable interval

### Request Flow

```
Client Request
     │
     ▼
FastAPI Router ──> Route Handler ──> Service Layer ──> Database
     │                                    │
     │                                    ▼
     │                              Business Logic
     │                              (calculations,
     │                               ML models)
     ▼
JSON Response
```

## Database Schema

### Entity Relationship Diagram

```
workspaces                    teams
┌──────────────────┐         ┌──────────────────┐
│ id (PK)          │         │ id (PK)          │
│ workspace_id     │         │ name             │
│ name             │         │ department       │
│ host             │         │ cost_center      │
│ cloud            │         │ manager_email    │
│ region           │         │ tag_patterns     │
│ status           │         └────────┬─────────┘
│ plan             │                  │ 1:N
└──────────────────┘         ┌────────▼─────────┐
                             │ team_members      │
                             │ id (PK)          │
                             │ team_id (FK)     │
                             │ email            │
                             │ role             │
                             └──────────────────┘

cost_records (hypertable)
┌───────────────────────┐      allocation_rules
│ id (PK)               │     ┌──────────────────┐
│ usage_date            │     │ id (PK)          │
│ workspace_id          │     │ team_id (FK)     │
│ sku_name              │     │ rule_type        │
│ cloud                 │     │ conditions       │
│ dbu_count             │     │ priority         │
│ dbu_rate              │     │ is_active        │
│ cost_usd              │     └──────────────────┘
│ cluster_id            │
│ job_id                │      cost_allocations
│ job_name              │     ┌──────────────────┐
│ user_email            │     │ id (PK)          │
│ tags (JSONB)          │     │ team_id (FK)     │
│ INDEX(date,workspace) │     │ period_start     │
│ INDEX(date,sku)       │     │ period_end       │
│ INDEX(user,date)      │     │ total_cost       │
└───────────────────────┘     │ breakdown (JSON) │
                              └──────────────────┘

cluster_info                   job_runs
┌──────────────────┐         ┌──────────────────┐
│ id (PK)          │         │ id (PK)          │
│ cluster_id       │         │ job_id           │
│ cluster_name     │         │ run_id           │
│ state            │         │ job_name         │
│ node_type        │         │ duration_seconds │
│ num_workers      │         │ dbu_consumed     │
│ photon_enabled   │         │ cost_usd         │
│ is_idle          │         │ schedule         │
│ total_cost_usd   │         └──────────────────┘
│ idle_time_hours  │
│ avg_cpu_util     │          alerts
└──────────────────┘         ┌──────────────────┐
                             │ id (PK)          │
recommendations              │ name             │
┌──────────────────┐         │ alert_type       │
│ id (PK)          │         │ threshold_value  │
│ type             │         │ notification_ch. │
│ severity         │         │ cooldown_minutes │
│ title            │         │ is_active        │
│ estimated_savings│         └────────┬─────────┘
│ status           │                  │ 1:N
└──────────────────┘         ┌────────▼─────────┐
                             │ alert_history     │
forecasts                    │ id (PK)          │
┌──────────────────┐         │ alert_id (FK)    │
│ id (PK)          │         │ triggered_at     │
│ forecast_date    │         │ status           │
│ predicted_cost   │         │ current_value    │
│ lower_bound      │         │ message          │
│ upper_bound      │         └──────────────────┘
│ model_type       │
└──────────────────┘          reports
                             ┌──────────────────┐
                             │ id (PK)          │
                             │ name             │
                             │ report_type      │
                             │ format           │
                             │ file_path        │
                             │ status           │
                             │ summary (JSON)   │
                             └──────────────────┘
```

### TimescaleDB Hypertable

The `cost_records` table is a TimescaleDB hypertable, partitioned by `usage_date`. This provides:
- Automatic time-based partitioning for fast range queries
- Efficient aggregation over time periods
- Built-in compression for historical data

### Key Indexes

| Table | Index | Purpose |
|-------|-------|---------|
| cost_records | `(usage_date, workspace_id)` | Dashboard workspace breakdown |
| cost_records | `(usage_date, sku_name)` | Dashboard SKU breakdown |
| cost_records | `(user_email, usage_date)` | User cost queries |
| cluster_info | `(workspace_id)` | Cluster listing by workspace |
| cluster_info | `(state)` | Filter running/idle clusters |

## Service Layer

### Cost Allocation Engine

Allocates cost records to teams using prioritized rules:

```
For each unallocated cost record:
  1. Check rules in priority order (lowest number = highest priority)
  2. First matching rule assigns the cost to that team
  3. If no rule matches, fall back to user-email -> team mapping
  4. If still unmatched, fall back to tag pattern matching
  5. Remaining costs go to "Unallocated"
```

**Rule types:**
- `tag_match` -- Match by resource tag key/value
- `user_match` -- Match by user email list
- `workspace_match` -- Match by workspace ID
- `cluster_match` -- Match by cluster name regex pattern
- `sku_match` -- Match by SKU name

### Anomaly Detection

Uses Z-score with a 7-day rolling window:

```
For each day's cost:
  1. Calculate mean and std of the previous 7 days
  2. Compute z-score = (value - mean) / std
  3. Flag as anomaly if |z-score| > sensitivity threshold

Severity levels:
  - |z| > 3.0  -> critical
  - |z| > 2.5  -> high
  - |z| > 2.0  -> medium
```

Detection runs across three dimensions:
- Overall daily spend
- Per-workspace spend
- Per-SKU spend

### Cost Forecasting

Two forecasting methods:

1. **Prophet** (primary) -- Facebook's time-series forecasting model
   - Handles seasonality (weekly, monthly patterns)
   - Produces 95% confidence intervals
   - Requires 30+ days of historical data

2. **Linear regression** (fallback) -- Used when Prophet is unavailable
   - Simple trend extrapolation using numpy
   - Confidence intervals based on standard deviation
   - Works with any amount of historical data

### Recommendation Engine

Scans clusters and generates optimization suggestions:

| Type | Trigger | Savings Estimate |
|------|---------|-----------------|
| Idle cluster | Running + no activity > 30 min | Hourly cost x idle hours |
| Right-sizing | CPU or memory utilization < 30% | 30% of current cost |
| Auto-termination | Running + auto-termination disabled | Based on typical idle time |

Cost estimation uses DBU rates from `constants.py` and approximate VM costs by instance type.

## Frontend Architecture

```
src/
├── App.tsx              # Router + sidebar navigation
├── main.tsx             # React entry point
├── index.css            # Global styles (dark theme)
├── api/
│   └── client.ts        # API client (fetch wrapper)
├── types/
│   └── index.ts         # TypeScript interfaces
├── components/
│   ├── StatCard.tsx      # KPI card (value + % change)
│   ├── CostTrendChart.tsx # Area chart (Recharts)
│   └── BreakdownChart.tsx # Bar + Pie charts
└── pages/
    ├── Dashboard.tsx        # Overview page
    ├── CostsPage.tsx        # Cost explorer
    ├── ClustersPage.tsx     # Cluster fleet
    ├── TeamsPage.tsx        # Team management
    ├── AlertsPage.tsx       # Alert configuration
    ├── ReportsPage.tsx      # Report generation
    ├── RecommendationsPage.tsx # Optimization tips
    └── ForecastPage.tsx     # Cost predictions
```

The frontend is a single-page app built with:
- **React 18** with functional components and hooks
- **TypeScript** for type safety
- **Vite** for fast development and bundling
- **React Router** for client-side routing
- **Recharts** for all data visualizations
- **Lucide React** for sidebar icons

The Vite dev server proxies `/api` requests to the FastAPI backend at `localhost:8000`.

## Scheduler

The background scheduler (`costpulse/schedulers/collector_scheduler.py`) runs two cycles:

**Collection cycle** (configurable interval, default 30s):
1. Collect billing data from System Tables
2. Collect cluster metadata
3. Collect job run data

**Analysis cycle** (runs after collection):
1. Check all active alerts
2. Generate recommendations
3. Run anomaly detection

## Technology Choices

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Database | TimescaleDB | Native time-series support on PostgreSQL; hypertables for cost data |
| API Framework | FastAPI | Async support, automatic OpenAPI docs, Pydantic validation |
| ORM | SQLAlchemy 2.0 | Async support, mature ecosystem, mapped_column pattern |
| Frontend | React + Vite | Fast development, rich ecosystem, TypeScript support |
| Charts | Recharts | React-native, composable, supports area/bar/pie |
| ML Forecasting | Prophet | Handles seasonality, minimal tuning, production-proven |
| CLI | Click + Rich | Beautiful terminal output, subcommand structure |
| Notifications | Slack SDK | Direct webhook integration, formatted messages |
