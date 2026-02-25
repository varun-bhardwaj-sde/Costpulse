# Deployment Guide

This guide covers deploying CostPulse in different environments.

## Docker Compose (Development / Small Teams)

The simplest way to run CostPulse. Suitable for development and teams with a single Databricks workspace.

### Prerequisites

- Docker Engine 20.10+
- Docker Compose v2.24.0+ (required for optional env_file syntax)
- 2 GB RAM minimum

### Steps

```bash
# 1. Clone and configure
git clone https://github.com/vrahad-analytics/costpulse.git
cd costpulse
cp .env.example .env
# Edit .env with your Databricks credentials

# 2. Start all services
docker-compose up -d

# 3. Verify services are running
docker-compose ps
```

**Expected output:**
```
NAME                STATUS              PORTS
costpulse-api       Up                  0.0.0.0:8000->8000/tcp
costpulse-db        Up (healthy)        0.0.0.0:5432->5432/tcp
costpulse-frontend  Up                  0.0.0.0:3000->3000/tcp
costpulse-redis     Up (healthy)        0.0.0.0:6379->6379/tcp
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| `costpulse-api` | 8000 | FastAPI backend |
| `costpulse-frontend` | 3000 | React dashboard |
| `costpulse-db` | 5432 | TimescaleDB (PostgreSQL) |
| `costpulse-redis` | 6379 | Redis cache |

### Managing Services

```bash
# View logs
docker-compose logs -f api
docker-compose logs -f timescaledb

# Restart a service
docker-compose restart api

# Stop all services
docker-compose down

# Stop and remove data volumes
docker-compose down -v
```

## Database Setup

### Running Migrations

After starting the database, run Alembic migrations to create the schema:

```bash
# If running locally
alembic upgrade head

# If running in Docker, exec into the API container
docker-compose exec api alembic upgrade head
```

### Creating New Migrations

When you modify models, generate a new migration:

```bash
alembic revision --autogenerate -m "description of changes"
alembic upgrade head
```

### Database Backup

```bash
# Backup
docker-compose exec timescaledb pg_dump -U costpulse costpulse > backup.sql

# Restore
docker-compose exec -T timescaledb psql -U costpulse costpulse < backup.sql
```

## Production Deployment

### Environment Variables

For production, set these securely:

```bash
# Strong secret key (generate with: openssl rand -hex 32)
API_SECRET_KEY=your_random_64_char_hex_string

# Strong database password
TIMESCALE_PASSWORD=your_secure_db_password

# Disable debug
DEBUG=false
```

### Running Behind a Reverse Proxy

Use Nginx or Traefik in front of CostPulse:

**Nginx example:**

```nginx
server {
    listen 80;
    server_name costpulse.yourcompany.com;

    # API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Running the API Without Docker

For production without Docker:

```bash
# Install production dependencies
pip install -e .

# Run with Gunicorn + Uvicorn workers
pip install gunicorn
gunicorn costpulse.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Running the Frontend in Production

Build the frontend and serve statically:

```bash
cd frontend
npm install
npm run build

# Serve the dist/ folder with any static file server
# Example with Python:
python -m http.server 3000 --directory dist

# Or with Nginx, serve dist/ as static files
```

## Scaling Considerations

### Database Performance

TimescaleDB handles time-series data efficiently with hypertables. For larger deployments:

- **Enable compression** on older data:
  ```sql
  ALTER TABLE cost_records SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'workspace_id'
  );
  SELECT add_compression_policy('cost_records', INTERVAL '7 days');
  ```

- **Add retention policy** to manage storage:
  ```sql
  SELECT add_retention_policy('cost_records', INTERVAL '365 days');
  ```

- **Continuous aggregates** for fast dashboard queries:
  ```sql
  CREATE MATERIALIZED VIEW daily_costs
  WITH (timescaledb.continuous) AS
  SELECT
    time_bucket('1 day', usage_date) AS day,
    workspace_id,
    sku_name,
    sum(cost_usd) AS total_cost,
    sum(dbu_count) AS total_dbu
  FROM cost_records
  GROUP BY day, workspace_id, sku_name;
  ```

### API Scaling

- Increase Gunicorn workers for more concurrent requests
- Use Redis for session caching and rate limiting
- Consider read replicas for the database if query load is high

### Data Collection Scaling

- Adjust `POLLING_INTERVAL` based on your needs (30s for real-time, 300s for cost savings)
- For multiple workspaces, collectors run sequentially per workspace

## Monitoring

### Health Check

The API exposes a health endpoint:

```bash
curl http://localhost:8000/api/v1/health
# {"status": "healthy", "service": "costpulse"}
```

Use this with your monitoring system (Datadog, Prometheus, etc.) to track uptime.

### Logs

All services output structured logs via `structlog`:

```bash
# API logs
docker-compose logs -f api

# Database logs
docker-compose logs -f timescaledb
```

### Database Monitoring

Connect to TimescaleDB and check:

```sql
-- Table sizes
SELECT hypertable_name, pg_size_pretty(total_bytes)
FROM timescaledb_information.hypertable;

-- Chunk count (partitions)
SELECT count(*) FROM timescaledb_information.chunks
WHERE hypertable_name = 'cost_records';

-- Recent data
SELECT max(usage_date), count(*) FROM cost_records
WHERE usage_date > now() - interval '1 day';
```

## Troubleshooting

### Database Connection Refused

```bash
# Check if TimescaleDB is running
docker-compose ps timescaledb

# Check logs
docker-compose logs timescaledb

# Verify connectivity
docker-compose exec timescaledb pg_isready -U costpulse
```

### API Not Starting

```bash
# Check API logs
docker-compose logs api

# Common issues:
# 1. Database not ready yet - wait for health check
# 2. Missing .env file - copy from .env.example
# 3. Invalid Databricks token - verify in .env
```

### Frontend Can't Connect to API

```bash
# Verify API is accessible
curl http://localhost:8000/api/v1/health

# Check VITE_API_URL in .env matches your setup
# For Docker Compose: VITE_API_URL=http://localhost:8000

# Check CORS settings in costpulse/api/main.py
# Frontend origins must be listed in allow_origins
```

### Migration Errors

```bash
# Check current migration state
alembic current

# If out of sync, stamp the current state
alembic stamp head

# Re-run migrations
alembic upgrade head
```

### High Memory Usage

If TimescaleDB uses too much memory:

```bash
# Adjust shared_buffers in postgresql.conf
# Recommended: 25% of available RAM

# Or set via Docker environment:
docker-compose exec timescaledb psql -U costpulse -c "SHOW shared_buffers;"
```
