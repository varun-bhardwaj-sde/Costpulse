# Configuration Reference

CostPulse is configured through environment variables. All settings can be placed in a `.env` file in the project root.

## Environment Variables

### Databricks Connection

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABRICKS_HOST` | Yes | -- | Databricks workspace URL (e.g., `https://adb-123.azuredatabricks.net`) |
| `DATABRICKS_TOKEN` | Yes | -- | Personal access token or service principal token |
| `DATABRICKS_ACCOUNT_ID` | No | -- | Account ID for account-level API calls |

### Database (TimescaleDB)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TIMESCALE_HOST` | No | `localhost` | TimescaleDB hostname |
| `TIMESCALE_PORT` | No | `5432` | TimescaleDB port |
| `TIMESCALE_DB` | No | `costpulse` | Database name |
| `TIMESCALE_USER` | No | `costpulse` | Database user |
| `TIMESCALE_PASSWORD` | Yes (prod) | `costpulse_dev` | Database password |

The database URL is constructed as:
```
postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}
```

### Redis

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis connection URL |

### API Server

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_HOST` | No | `0.0.0.0` | API server bind address |
| `API_PORT` | No | `8000` | API server port |
| `API_SECRET_KEY` | Yes (prod) | `change_this_secret_key` | API key for protected endpoints |

### Feature Flags

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEBUG` | No | `false` | Enable debug mode (verbose logging) |
| `POLLING_INTERVAL` | No | `30` | Data collection interval in seconds |
| `ENABLE_FORECASTING` | No | `true` | Enable ML cost forecasting |
| `ENABLE_ANOMALY_DETECTION` | No | `true` | Enable anomaly detection |

### Notifications

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SLACK_WEBHOOK_URL` | No | -- | Slack incoming webhook URL for alert notifications |

### Storage

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REPORTS_DIR` | No | `/tmp/costpulse_reports` | Directory for generated report files |

### Frontend

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_URL` | No | `http://localhost:8000` | API URL for the React frontend |

## Example .env File

```bash
# ============================================
# CostPulse Configuration
# ============================================

# -- Databricks (Required) --
DATABRICKS_HOST=https://adb-1234567890.azuredatabricks.net
DATABRICKS_TOKEN=dapi_abcdef1234567890
DATABRICKS_ACCOUNT_ID=

# -- Database --
TIMESCALE_HOST=localhost
TIMESCALE_PORT=5432
TIMESCALE_DB=costpulse
TIMESCALE_USER=costpulse
TIMESCALE_PASSWORD=your_secure_password

# -- Redis --
REDIS_URL=redis://localhost:6379/0

# -- API --
API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY=your_random_secret_key_here

# -- Feature Flags --
DEBUG=false
POLLING_INTERVAL=30
ENABLE_FORECASTING=true
ENABLE_ANOMALY_DETECTION=true

# -- Notifications --
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00/B00/xxx

# -- Storage --
REPORTS_DIR=/var/costpulse/reports

# -- Frontend --
VITE_API_URL=http://localhost:8000
```

## Docker Compose Environment

When running with Docker Compose, the following defaults are pre-configured:

```yaml
# TimescaleDB (set in docker-compose.yml)
POSTGRES_DB: costpulse
POSTGRES_USER: costpulse
POSTGRES_PASSWORD: costpulse_dev

# API reads from .env file
# Frontend reads VITE_API_URL from .env
```

## Setting Up Slack Notifications

1. Go to https://api.slack.com/apps and create a new app
2. Enable **Incoming Webhooks**
3. Add a new webhook to your desired channel
4. Copy the webhook URL and set it as `SLACK_WEBHOOK_URL`

Alert notifications will be sent as formatted Slack messages with:
- Alert name and type
- Current value vs threshold
- Team context

## API Authentication

Protected endpoints require the `X-API-Key` header:

```bash
curl -H "X-API-Key: your_api_secret_key" http://localhost:8000/api/v1/...
```

The key is validated against the `API_SECRET_KEY` environment variable. Most read endpoints are open by default; write operations and sensitive endpoints may require authentication.

## Constants and Rates

DBU rates and VM costs are configured in `costpulse/core/constants.py`. These are not environment variables but can be modified directly:

```python
# costpulse/core/constants.py
DBU_RATES = {
    "JOBS_COMPUTE": 0.15,
    "JOBS_COMPUTE_PHOTON": 0.30,
    "ALL_PURPOSE_COMPUTE": 0.55,
    # ... more SKUs
}

VM_COSTS = {
    "i3.xlarge": 0.312,
    "m5.xlarge": 0.192,
    # ... more instance types
}
```

To override rates for your specific Databricks contract, edit these values and restart the services.
