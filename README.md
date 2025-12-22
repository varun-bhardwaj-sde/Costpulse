# CostPulse

**Real-time Databricks cost intelligence platform. Stop flying blind - know your costs before the bill arrives.**

[![PyPI version](https://badge.fury.io/py/costpulse.svg)](https://badge.fury.io/py/costpulse)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Overview

CostPulse is an open-source, real-time cost intelligence platform for Databricks. It provides:

- **Real-time cost monitoring** - Sub-minute cost updates from Databricks System Tables
- **Predictive forecasting** - ML-powered cost predictions using Prophet
- **Pre-execution estimates** - Know query costs before running them
- **Anomaly detection** - Automated alerts for cost spikes and unusual patterns
- **Developer-first CLI** - Full functionality from your terminal
- **FinOps FOCUS export** - Industry-standard cost data format

## Features

### Open Source Core

- ✅ Real-time cost streaming (30-second intervals)
- ✅ Basic cost dashboard
- ✅ CLI tool (`costpulse query`, `costpulse estimate`, `costpulse alert`)
- ✅ Single workspace support
- ✅ 7-day data retention
- ✅ Basic anomaly detection
- ✅ Slack notifications
- ✅ FinOps FOCUS export

### Enterprise Features (Coming Soon)

- 🔒 Multi-workspace aggregation
- 🔒 Advanced ML forecasting
- 🔒 Pre-execution cost estimates
- 🔒 SSO/SAML integration
- 🔒 365-day retention
- 🔒 Custom dashboards
- 🔒 Chargeback reports
- 🔒 SLA-backed support

## Quick Start

### Installation

```bash
pip install costpulse
```

### Configuration

```bash
# Initialize configuration
costpulse config init

# Or manually create .env file
cp .env.example .env
# Edit .env with your Databricks credentials
```

### Usage

```bash
# View today's costs
costpulse query today

# Watch costs in real-time
costpulse watch

# Export to JSON
costpulse query today --format json

# Export to CSV
costpulse query today --format csv > costs.csv
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CostPulse Platform                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐     ┌──────────────┐                     │
│  │  Databricks  │────▶│  Data        │                     │
│  │  System      │     │  Collection  │                     │
│  │  Tables      │     │  Layer       │                     │
│  └──────────────┘     └──────┬───────┘                     │
│                              │                              │
│                              ▼                              │
│                       ┌──────────────┐                      │
│                       │  Processing  │                      │
│                       │  Engine      │                      │
│                       └──────┬───────┘                      │
│                              │                              │
│                              ▼                              │
│                       ┌──────────────┐                      │
│                       │  TimescaleDB │                      │
│                       │  + Redis     │                      │
│                       └──────┬───────┘                      │
│                              │                              │
│                              ▼                              │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────┐│
│  │  CLI Tool    │────▶│  API Layer   │────▶│  Dashboard  ││
│  └──────────────┘     └──────────────┘     └─────────────┘│
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

- **Python 3.10+** - Core application
- **Poetry** - Dependency management
- **FastAPI** - REST/WebSocket API
- **TimescaleDB** - Time-series storage
- **Redis** - Caching and real-time updates
- **Click + Rich** - Beautiful CLI
- **Prophet** - ML forecasting
- **Databricks SDK** - API integration

## Development

### Prerequisites

- Python 3.10+
- Poetry
- Docker & Docker Compose (for local development)
- Databricks workspace with System Tables enabled

### Setup

```bash
# Clone the repository
git clone https://github.com/vrahad-analytics/costpulse.git
cd costpulse

# Install dependencies
poetry install

# Start local infrastructure (TimescaleDB + Redis)
docker-compose up -d

# Run the CLI
poetry run costpulse --help
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=costpulse

# Run specific test file
poetry run pytest tests/unit/test_cost_calculator.py
```

### Code Quality

```bash
# Format code
poetry run black costpulse tests

# Lint code
poetry run ruff costpulse tests

# Type checking
poetry run mypy costpulse
```

## Data Sources

CostPulse collects data from:

1. **System Tables** (`system.billing.usage`) - Primary source for billing data
2. **Cluster API** - Real-time cluster state
3. **SQL Warehouses API** - Warehouse usage
4. **Jobs API** - Job run information

## DBU Rates

CostPulse uses the following DBU rates (as of December 2024):

| SKU | Rate (USD) |
|-----|------------|
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

*Note: Rates are subject to change. See [costpulse/core/constants.py](costpulse/core/constants.py) for current values.*

## Configuration

All configuration is managed via environment variables. See [.env.example](.env.example) for all available options.

### Required

- `DATABRICKS_HOST` - Your Databricks workspace URL
- `DATABRICKS_TOKEN` - Databricks personal access token

### Optional

- `TIMESCALE_HOST` - TimescaleDB host (default: localhost)
- `TIMESCALE_PORT` - TimescaleDB port (default: 5432)
- `REDIS_URL` - Redis connection URL
- `POLLING_INTERVAL` - Polling interval in seconds (default: 30)
- `ENABLE_FORECASTING` - Enable ML forecasting (default: true)
- `ENABLE_ANOMALY_DETECTION` - Enable anomaly detection (default: true)

## CLI Reference

### Configuration Commands

```bash
costpulse config init              # Initialize configuration
costpulse config set <key> <value> # Set configuration value
costpulse config show              # Show current configuration
```

### Query Commands

```bash
costpulse query today              # Today's costs
costpulse query yesterday          # Yesterday's costs
costpulse query --from DATE --to DATE  # Date range
costpulse query --by user          # Group by user
costpulse query --by cluster       # Group by cluster
costpulse query --format json      # JSON output
costpulse query --format csv       # CSV output
```

### Watch Command

```bash
costpulse watch                    # Live cost stream
costpulse watch --refresh 30       # Custom refresh interval
```

## Roadmap

### Phase 1: Foundation ✅ (Current)
- [x] Project scaffolding
- [x] Databricks SDK integration
- [x] System Tables collector
- [x] Basic cost calculator
- [x] CLI framework

### Phase 2: API & Real-time (Next)
- [ ] FastAPI REST endpoints
- [ ] WebSocket real-time updates
- [ ] Redis caching
- [ ] Anomaly detection

### Phase 3: ML & Forecasting
- [ ] Prophet integration
- [ ] Query cost estimation
- [ ] Forecast accuracy tracking

### Phase 4: Dashboard
- [ ] React + TypeScript UI
- [ ] Real-time charts
- [ ] Anomaly alerts UI

### Phase 5: Enterprise
- [ ] Multi-workspace support
- [ ] SSO/SAML
- [ ] Advanced chargeback
- [ ] Kubernetes Helm chart

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Support

- 📧 Email: contact@vrahad.com
- 🐛 Issues: [GitHub Issues](https://github.com/vrahad-analytics/costpulse/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/vrahad-analytics/costpulse/discussions)

## Acknowledgments

- Databricks for System Tables and comprehensive APIs
- FinOps Foundation for the FOCUS specification
- Facebook Prophet for forecasting capabilities

---

**Built with ❤️ by Vrahad Analytics**
