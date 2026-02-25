# CostPulse

**FinOps-in-a-box for Databricks. Real-time cost intelligence, team chargeback, anomaly detection, and optimization recommendations -- all in one platform.**

[![PyPI version](https://badge.fury.io/py/costpulse.svg)](https://badge.fury.io/py/costpulse)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## What is CostPulse?

CostPulse is an open-source FinOps platform built specifically for Databricks customers spending $50K-$500K/month. It answers the questions every data team asks:

- **"Who is spending what?"** -- Cost attribution by team, user, workspace, and job
- **"Is this normal?"** -- Anomaly detection catches cost spikes before the bill arrives
- **"Where can we save?"** -- Recommendations for idle clusters, right-sizing, and auto-termination
- **"What will next month look like?"** -- ML-powered cost forecasting with confidence intervals

## Features

| Feature | Description |
|---------|-------------|
| **Cost Dashboard** | Real-time overview with cost trends, breakdowns by workspace/SKU/user/job |
| **Team Chargeback** | Rule-based cost allocation to teams with showback/chargeback reports |
| **Anomaly Detection** | Z-score algorithm detects cost spikes and drops with severity levels |
| **Budget Alerts** | Configurable alerts with Slack and email notifications, cooldown support |
| **Cluster Monitoring** | Track cluster fleet -- idle detection, utilization, Photon usage |
| **Recommendations** | Auto-generated optimization suggestions with estimated savings |
| **Cost Forecasting** | Prophet + linear regression forecasts with confidence intervals |
| **Tag Compliance** | Enforce required tags (team, environment, project, cost_center) |
| **Reports** | Generate CSV, Excel, and PDF reports on demand |
| **CLI Tool** | Query costs, watch real-time data, and manage configuration from terminal |
| **REST API** | Full-featured API with 40+ endpoints across 11 modules |
| **React Dashboard** | Dark-themed UI with interactive charts and data tables |

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/aviral-bhardwaj/Costpulse.git
cd costpulse
pip install -e .
```

### 2. Start infrastructure

```bash
docker-compose up -d   # Starts TimescaleDB, Redis, API, and frontend
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env with your Databricks workspace URL and token
```

### 4. Run database migrations

```bash
alembic upgrade head
```

### 5. Access the platform

- **Dashboard**: http://localhost:3000
- **API**: http://localhost:8000/docs (interactive Swagger UI)
- **CLI**: `costpulse query today`

> For detailed setup instructions, see [docs/getting-started.md](docs/getting-started.md)

## Architecture

```
                    ┌─────────────────────────────┐
                    │   React Dashboard (:3000)    │
                    │   Charts / Tables / Alerts   │
                    └──────────────┬──────────────┘
                                   │ HTTP
                    ┌──────────────▼──────────────┐
                    │   FastAPI REST API (:8000)   │
                    │   40+ endpoints, 11 modules  │
                    └──────────────┬──────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                     │
   ┌──────────▼─────────┐ ┌───────▼───────┐ ┌──────────▼─────────┐
   │   Service Layer     │ │  Collectors   │ │    Scheduler       │
   │   - Allocation      │ │  - Billing    │ │  - Auto-collect    │
   │   - Anomaly Det.    │ │  - Clusters   │ │  - Auto-analyze    │
   │   - Alerts          │ │  - Jobs       │ │  - Alert checks    │
   │   - Forecasting     │ │  - Warehouses │ └────────────────────┘
   │   - Recommendations │ │  - Users      │
   │   - Reports         │ └───────┬───────┘
   │   - Tag Compliance  │         │ Databricks SDK
   └──────────┬──────────┘         │
              │            ┌───────▼───────┐
              │            │  Databricks   │
   ┌──────────▼──────────┐ │  System Tables│
   │  TimescaleDB + Redis│ │  + REST APIs  │
   │  Time-series store  │ └───────────────┘
   └─────────────────────┘
```

## Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/getting-started.md) | Installation, setup, first steps |
| [Configuration](docs/configuration.md) | All environment variables and settings |
| [API Reference](docs/api-reference.md) | Complete REST API documentation with examples |
| [Architecture](docs/architecture.md) | System design, data models, service layer |
| [Deployment](docs/deployment.md) | Docker, production setup, scaling |

## CLI Usage

```bash
# View today's costs
costpulse query today

# Watch costs in real-time (refreshes every 30s)
costpulse watch

# Export as JSON
costpulse query today --format json

# Export as CSV
costpulse query today --format csv > costs.csv

# Initialize configuration interactively
costpulse config init
```

## API Examples

```bash
# Dashboard overview (last 30 days)
curl http://localhost:8000/api/v1/dashboard/overview

# Cost trend (daily granularity)
curl http://localhost:8000/api/v1/dashboard/cost-trend?days=30&granularity=daily

# Generate cost forecast
curl -X POST "http://localhost:8000/api/v1/forecasts/generate?horizon_days=30"

# Check tag compliance
curl http://localhost:8000/api/v1/tags/compliance

# Generate recommendations
curl -X POST http://localhost:8000/api/v1/recommendations/generate

# Health check
curl http://localhost:8000/api/v1/health
```

> See [docs/api-reference.md](docs/api-reference.md) for full documentation with request/response examples.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.10+, FastAPI, SQLAlchemy 2.0 |
| Database | TimescaleDB (PostgreSQL + time-series) |
| Cache | Redis |
| Frontend | React 18, TypeScript, Vite, Recharts |
| ML | Prophet, scikit-learn |
| CLI | Click, Rich |
| Databricks | Databricks SDK, System Tables |
| Notifications | Slack SDK, SMTP |
| Containers | Docker, Docker Compose |

## Data Sources

CostPulse collects data from these Databricks sources:

| Source | Data |
|--------|------|
| `system.billing.usage` | Billing records, DBU consumption, cost by SKU |
| Clusters API | Cluster state, utilization, idle detection |
| Jobs API | Job runs, durations, task counts |
| SQL Warehouses API | Warehouse size, sessions, serverless status |
| Users/Groups API | Team auto-discovery from workspace groups |

## DBU Rates

Current rates (December 2024):

| SKU | Rate (USD/DBU) |
|-----|---------------|
| Jobs Compute | $0.15 |
| Jobs Compute (Photon) | $0.30 |
| All-Purpose Compute | $0.55 |
| All-Purpose Compute (Photon) | $1.10 |
| SQL Compute | $0.22 |
| SQL Compute (Serverless) | $0.70 |
| Delta Live Tables (Core) | $0.20 |
| Delta Live Tables (Pro) | $0.25 |
| Delta Live Tables (Advanced) | $0.36 |
| Model Serving | $0.07 |

*Rates configurable in [costpulse/core/constants.py](costpulse/core/constants.py).*

## Development

```bash
# Install with dev dependencies
poetry install

# Run tests (67 tests)
pytest tests/ -v

# Run with coverage
pytest --cov=costpulse tests/

# Code formatting
poetry run black costpulse tests

# Linting
poetry run ruff costpulse tests

# Type checking
poetry run mypy costpulse
```

## Roadmap

- [x] **Phase 1**: Foundation -- Databricks SDK, System Tables collector, CLI, cost calculator
- [x] **Phase 2**: Platform -- FastAPI API, database models, services, React dashboard, Docker
- [ ] **Phase 3**: Intelligence -- Advanced ML forecasting, query cost estimation, accuracy tracking
- [ ] **Phase 4**: Enterprise -- Multi-workspace, SSO/SAML, Kubernetes Helm chart
- [ ] **Phase 5**: Automation -- Auto-scaling policies, scheduled shutdowns, Terraform integration

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes and add tests
4. Run `pytest` and `ruff` to verify
5. Commit and push (`git push origin feature/your-feature`)
6. Open a Pull Request

## License

Apache License 2.0 -- see [LICENSE](LICENSE) for details.

## Support

- Issues: [GitHub Issues](https://github.com/aviral-bhardwaj/Costpulse/issues)
- Discussions: [GitHub Discussions](https://github.com/aviral-bhardwaj/Costpulse/costpulse/discussions)
- Email: contact@vrahad.com

---

**Built by Vrahad Analytics**
