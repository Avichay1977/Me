# Deployment Metrics & Monitoring Scripts

Production-grade deployment metrics collection, analysis, and alerting system.

## Quick Start

```bash
# 1. Install dependencies
pip install flask requests

# 2. Run a deployment (metrics are automatically collected)
./deploy.sh

# 3. Start the metrics API server
./analyze_deployment_metrics.py ./metrics/deployment_metrics.jsonl --server --port 8080

# 4. View metrics summary
./analyze_deployment_metrics.py ./metrics/deployment_metrics.jsonl --days 30
```

## Components

### 1. `deploy.sh` - Deployment Script

Enhanced deployment script with full observability. Logs comprehensive metrics in JSONL format.

**Features:**
- Automatic backup before deployment
- Health checks with configurable retries
- Smoke tests with latency measurement
- Automatic rollback on failure
- Slack/webhook notifications

**Usage:**
```bash
# Basic deployment
./deploy.sh

# With custom configuration
ENV=staging VERSION=1.2.3 ./deploy.sh

# With Slack notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/... ./deploy.sh
```

**Environment Variables:**
| Variable | Default | Description |
|----------|---------|-------------|
| `ENV` | production | Environment name |
| `SERVICE` | cubase-script-assistant | Service name |
| `VERSION` | git tag | Version being deployed |
| `HEALTH_CHECK_URL` | http://localhost:5001/ | Health check endpoint |
| `HEALTH_CHECK_RETRIES` | 5 | Number of health check attempts |
| `SLACK_WEBHOOK_URL` | - | Slack webhook for notifications |

### 2. `analyze_deployment_metrics.py` - Metrics Analyzer & API

Analyzes deployment metrics and provides both CLI and REST API interfaces.

**CLI Usage:**
```bash
# Summary report
./analyze_deployment_metrics.py metrics.jsonl --days 30

# JSON output
./analyze_deployment_metrics.py metrics.jsonl --days 30 --json
```

**API Server:**
```bash
# Start server
./analyze_deployment_metrics.py metrics.jsonl --server --port 8080
```

**API Endpoints:**

| Endpoint | Description |
|----------|-------------|
| `GET /api/summary` | Comprehensive metrics summary |
| `GET /api/success_rate` | Deployment success rate |
| `GET /api/latency` | Latency statistics (avg, p50, p95, p99) |
| `GET /api/mttr` | Mean Time To Rollback |
| `GET /api/deployment_frequency` | Deployment frequency stats |
| `GET /api/recent` | Recent deployments list |
| `GET /api/anomalies` | Anomaly detection results |
| `GET /api/compare?deployment_id1=X&deployment_id2=Y` | Compare deployments |
| `GET /api/health_timeline/<id>` | Health check timeline |
| `GET /api/alerts/evaluate` | Current alert status |
| `GET /api/trends` | Success rate trends |
| `GET /api/versions` | Success rate by version |

All endpoints accept `?days=N` parameter to specify time range.

### 3. `deployment_health_monitor.py` - Health Monitor

Continuous monitoring script that checks metrics and sends alerts.

**Usage:**
```bash
# Manual run
SLACK_WEBHOOK_URL=https://... ./deployment_health_monitor.py

# Via cron (every hour)
0 * * * * /path/to/deployment_health_monitor.py
```

**Supported Alert Channels:**
- Slack
- Microsoft Teams
- PagerDuty (for critical alerts)

### 4. `daily_deployment_digest.py` - Daily Reports

Sends daily summary reports to Slack/Teams.

**Usage:**
```bash
# Yesterday's summary
./daily_deployment_digest.py

# Last 7 days
DIGEST_DAYS=7 ./daily_deployment_digest.py
```

## Metrics Format

All metrics are stored in JSONL format (one JSON object per line):

```json
{
  "timestamp": "2025-01-25T10:30:00+00:00",
  "deployment_id": "20250125103000-a1b2",
  "env": "production",
  "service": "cubase-script-assistant",
  "version": "1.2.3",
  "triggered_by": "jenkins",
  "user": "john.doe",
  "git_commit": "a1b2c3d",
  "git_branch": "main",
  "elapsed_from_start_ms": 45678,
  "severity": "INFO",
  "error_code": null,
  "trace_id": "xyz789",
  "event": "deployment_completed",
  "data": {"status": "success"}
}
```

**Event Types:**
- `deployment_started`
- `backup_completed`
- `deployment_executed`
- `health_check_attempt`
- `health_check_passed` / `health_check_failed`
- `smoke_test_completed`
- `deployment_decision`
- `rollback_started` / `rollback_completed`
- `deployment_completed`

## Grafana Dashboard

Import `dashboards/deployment-metrics.json` into Grafana.

**Prerequisites:**
1. Install JSON API datasource plugin
2. Configure datasource pointing to the metrics API
3. Set `METRICS_API` variable in dashboard

**Dashboard Panels:**
- Success Rate (stat)
- Rollback Count (stat)
- MTTR (stat)
- Avg Latency (stat)
- Active Alerts (table)
- Anomaly Detection (table)
- Success Rate Trend (timeseries)
- Latency Distribution (barchart)
- Success Rate by Version (table)
- Deployments by Day of Week (piechart)
- Recent Deployments (table)
- Rollback Duration (barchart)

## Cron Setup

See `crontab.example` for recommended cron configuration:

```bash
# Install crontab entries
crontab crontab.example

# Or edit existing crontab
crontab -e
```

## Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your values
export $(grep -v '^#' .env | xargs)
```

## Alert Thresholds

Default alert thresholds:

| Alert | Threshold | Severity |
|-------|-----------|----------|
| LOW_SUCCESS_RATE | < 80% | high |
| HIGH_LATENCY | > 20s | medium |
| FREQUENT_ROLLBACKS | >= 3 in 7 days | critical |
| ANOMALIES_DETECTED | z-score > 2 | medium |

## Architecture

```
                    +-----------------+
                    |  deploy.sh      |
                    |  (Bash script)  |
                    +--------+--------+
                             |
                             | writes
                             v
                    +--------+--------+
                    | metrics.jsonl   |
                    | (JSONL file)    |
                    +--------+--------+
                             |
                             | reads
                             v
        +--------------------+--------------------+
        |                    |                    |
        v                    v                    v
+-------+-------+   +--------+--------+   +-------+-------+
| analyze...py  |   | health_monitor  |   | daily_digest  |
| --server      |   | .py             |   | .py           |
+-------+-------+   +--------+--------+   +-------+-------+
        |                    |                    |
        | HTTP               | HTTP               | HTTP
        v                    v                    v
+-------+-------+   +--------+--------+   +-------+-------+
| Grafana       |   | Slack/Teams/    |   | Slack/Teams   |
| Dashboard     |   | PagerDuty       |   |               |
+---------------+   +-----------------+   +---------------+
```

## Troubleshooting

**Metrics file not found:**
```bash
mkdir -p metrics
touch metrics/deployment_metrics.jsonl
```

**API server not responding:**
```bash
# Check if running
pgrep -f analyze_deployment_metrics

# Start in background
nohup ./analyze_deployment_metrics.py metrics.jsonl --server &
```

**No alerts being sent:**
1. Verify webhook URLs are correct
2. Check network connectivity
3. Review logs for errors

**High memory usage:**
- Metrics file may be too large
- Consider archiving old metrics
- Use `--days` parameter to limit analysis scope
