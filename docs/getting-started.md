# Getting Started with CostPulse

This guide walks you through installing, configuring, and running CostPulse for the first time.

## Prerequisites

Before you begin, make sure you have:

- **Python 3.10+** installed
- **Docker and Docker Compose v2.24.0+** for running TimescaleDB and Redis
- **A Databricks workspace** with:
  - A personal access token (PAT) or service principal
  - System Tables enabled (for billing data)
  - Workspace admin access (recommended, for full data collection)

## Installation

### Option A: Docker Compose (Recommended)

This starts the full platform -- database, API, and frontend:

```bash
git clone https://github.com/vrahad-analytics/costpulse.git
cd costpulse

# Copy and edit environment configuration
cp .env.example .env
# Edit .env with your Databricks credentials (see Configuration below)

# Start all services
docker-compose up -d
```

Services will be available at:
- **Dashboard**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **TimescaleDB**: localhost:5432
- **Redis**: localhost:6379

### Option B: Local Development

For development or if you want to run components individually:

```bash
git clone https://github.com/vrahad-analytics/costpulse.git
cd costpulse

# Install Python dependencies
pip install -e .
# Or with Poetry:
poetry install

# Start only the database and cache
docker-compose up -d timescaledb redis

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn costpulse.api.main:app --host 0.0.0.0 --port 8000 --reload

# In another terminal -- start the frontend
cd frontend
npm install
npm run dev
```

### Option C: CLI Only

If you only need the command-line tool (no database required for basic queries):

```bash
pip install costpulse

# Initialize configuration
costpulse config init

# Query costs immediately
costpulse query today
```

## Configuration

### Required Settings

Create a `.env` file in the project root with at minimum:

```bash
# Your Databricks workspace URL
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com

# Personal access token or service principal token
DATABRICKS_TOKEN=dapi_your_token_here
```

### Database Settings

If using the full platform (default values work with Docker Compose):

```bash
TIMESCALE_HOST=localhost
TIMESCALE_PORT=5432
TIMESCALE_DB=costpulse
TIMESCALE_USER=costpulse
TIMESCALE_PASSWORD=costpulse_dev
```

### API Settings

```bash
API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY=change_this_in_production
```

> For the complete list of settings, see [configuration.md](configuration.md).

## First Steps

### Step 1: Verify the connection

Check that the API is running:

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{"status": "healthy", "service": "costpulse"}
```

### Step 2: View costs via CLI

```bash
# Today's costs in a formatted table
costpulse query today

# As JSON for scripting
costpulse query today --format json
```

### Step 3: Open the dashboard

Open http://localhost:3000 in your browser. The dashboard shows:

- **Cost Overview** -- Total spend, DBU consumption, period-over-period change
- **Cost Trend** -- Daily/weekly/monthly cost chart
- **Breakdown** -- Costs by workspace and SKU type

### Step 4: Register your workspace

Register your Databricks workspace so CostPulse can track it:

```bash
curl -X POST http://localhost:8000/api/v1/workspaces/ \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "your-workspace-id",
    "name": "Production",
    "host": "https://your-workspace.cloud.databricks.com",
    "cloud": "aws",
    "region": "us-east-1"
  }'
```

### Step 5: Set up alerts

Create a budget alert to get notified when monthly spend exceeds a threshold:

```bash
curl -X POST http://localhost:8000/api/v1/alerts/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Monthly Budget Alert",
    "alert_type": "budget_threshold",
    "threshold_value": 50000,
    "threshold_type": "absolute",
    "notification_channels": {"slack": true},
    "cooldown_minutes": 60
  }'
```

### Step 6: Generate recommendations

Scan your clusters for optimization opportunities:

```bash
curl -X POST http://localhost:8000/api/v1/recommendations/generate
```

Then view them:

```bash
curl http://localhost:8000/api/v1/recommendations/
```

### Step 7: Check tag compliance

See which resources are missing required tags:

```bash
curl http://localhost:8000/api/v1/tags/compliance
```

## Creating a Databricks Token

1. Log in to your Databricks workspace
2. Click your username in the top-right corner
3. Select **Settings** > **Developer** > **Access Tokens**
4. Click **Generate New Token**
5. Give it a description like "CostPulse" and set an appropriate lifetime
6. Copy the token and add it to your `.env` file as `DATABRICKS_TOKEN`

**Required permissions** for the token:

| Permission | Purpose |
|-----------|---------|
| Workspace access | Read cluster, job, and warehouse information |
| System Tables access | Read `system.billing.usage` for cost data |
| SQL warehouse access | Run queries against system tables |

## Enabling System Tables

CostPulse reads cost data from Databricks System Tables. To enable them:

1. You must be a Databricks **account admin**
2. Go to **Account Console** > **Settings** > **Feature Enablement**
3. Enable **System Tables**
4. The `system.billing.usage` table will populate within 24 hours

If System Tables are not yet available, CostPulse will use the Cluster and Jobs APIs for cost estimation.

## Troubleshooting

### "Connection refused" when accessing the API

Make sure Docker services are running:
```bash
docker-compose ps
```
All services should show as "Up". If TimescaleDB is still starting, wait for the health check to pass.

### "Invalid or missing API key" error

For protected endpoints, pass the API key header:
```bash
curl -H "X-API-Key: your_api_secret_key" http://localhost:8000/api/v1/...
```
The key is set via the `API_SECRET_KEY` environment variable.

### Database migration errors

If you see table-related errors, ensure migrations have run:
```bash
alembic upgrade head
```

### Databricks SDK import errors

If you see `_cffi_backend` errors, this is a known issue in some environments. The API and frontend work independently of the Databricks SDK -- only the data collectors require it.

## Next Steps

- [Configuration Reference](configuration.md) -- All available settings
- [API Reference](api-reference.md) -- Full endpoint documentation
- [Architecture Guide](architecture.md) -- System design and data flow
- [Deployment Guide](deployment.md) -- Production deployment
