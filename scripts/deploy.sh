#!/usr/bin/env bash
#
# Enhanced Deployment Script with Metrics Logging
# Production-grade deployment with full observability
#

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Deployment configuration (can be overridden via environment)
ENV="${ENV:-production}"
SERVICE="${SERVICE:-cubase-script-assistant}"
VERSION="${VERSION:-$(git describe --tags --always 2>/dev/null || echo 'unknown')}"
DEPLOYMENT_ID="${DEPLOYMENT_ID:-$(date +%Y%m%d%H%M%S)-$(printf '%04x' $RANDOM)}"

# Metrics configuration
METRICS_DIR="${METRICS_DIR:-$PROJECT_ROOT/metrics}"
METRICS_LOG="${METRICS_LOG:-$METRICS_DIR/deployment_metrics.jsonl}"
DEPLOYMENT_START_TIME=$(date +%s%3N)

# Alert configuration
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"

# Health check configuration
HEALTH_CHECK_URL="${HEALTH_CHECK_URL:-http://localhost:5001/}"
HEALTH_CHECK_RETRIES="${HEALTH_CHECK_RETRIES:-5}"
HEALTH_CHECK_INTERVAL="${HEALTH_CHECK_INTERVAL:-2}"

# Smoke test configuration
SMOKE_TEST_ITERATIONS="${SMOKE_TEST_ITERATIONS:-3}"
LATENCY_THRESHOLD="${LATENCY_THRESHOLD:-20}"

# Rollback configuration
SHOULD_ROLLBACK=0
ROLLBACK_REASON=""
PREVIOUS_VERSION=""

# =============================================================================
# Metrics Logging Functions
# =============================================================================

ensure_metrics_dir() {
    mkdir -p "$METRICS_DIR"
}

log_metric() {
    local event="$1"
    local data="$2"
    local severity="${SEVERITY:-INFO}"

    local now=$(date +%s%3N)
    local elapsed=$((now - DEPLOYMENT_START_TIME))

    local entry=$(cat <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "deployment_id": "$DEPLOYMENT_ID",
  "env": "$ENV",
  "service": "$SERVICE",
  "version": "$VERSION",
  "triggered_by": "${TRIGGERED_BY:-manual}",
  "user": "${DEPLOY_USER:-$(whoami)}",
  "git_commit": "$(git -C "$PROJECT_ROOT" rev-parse --short HEAD 2>/dev/null || echo 'unknown')",
  "git_branch": "$(git -C "$PROJECT_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')",
  "elapsed_from_start_ms": $elapsed,
  "severity": "$severity",
  "error_code": ${ERROR_CODE:-null},
  "parent_deployment_id": ${PARENT_DEPLOYMENT_ID:-null},
  "trace_id": "${TRACE_ID:-$(uuidgen 2>/dev/null || echo "trace-$DEPLOYMENT_ID")}",
  "event": "$event",
  "data": $data
}
EOF
)

    # Compact JSON (remove newlines for JSONL format)
    echo "$entry" | tr -d '\n' | sed 's/  */ /g' >> "$METRICS_LOG"
    echo "" >> "$METRICS_LOG"

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$severity] $event"
}

# =============================================================================
# Alert Functions
# =============================================================================

send_alert() {
    local severity="$1"
    local title="$2"
    local message="$3"

    [[ -z "$SLACK_WEBHOOK_URL" ]] && return 0

    local color
    case "$severity" in
        critical) color="#FF0000" ;;
        warning)  color="#FFA500" ;;
        info)     color="#00FF00" ;;
        *)        color="#808080" ;;
    esac

    local payload=$(cat <<EOF
{
  "attachments": [{
    "color": "$color",
    "title": "$title",
    "text": "$message",
    "fields": [
      {"title": "Deployment ID", "value": "$DEPLOYMENT_ID", "short": true},
      {"title": "Environment", "value": "$ENV", "short": true},
      {"title": "Version", "value": "$VERSION", "short": true},
      {"title": "Service", "value": "$SERVICE", "short": true},
      {"title": "Timestamp", "value": "$(date -Iseconds)", "short": true},
      {"title": "User", "value": "${DEPLOY_USER:-$(whoami)}", "short": true}
    ],
    "actions": [{
      "type": "button",
      "text": "View Dashboard",
      "url": "$GRAFANA_URL/d/deployment-metrics?var-deployment_id=$DEPLOYMENT_ID"
    }]
  }]
}
EOF
)

    curl -s -X POST -H 'Content-Type: application/json' \
        -d "$payload" "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 || true
}

# =============================================================================
# Deployment Functions
# =============================================================================

backup_current_version() {
    echo "Creating backup of current version..."

    local start_time=$(date +%s%3N)

    # Store current version for potential rollback
    PREVIOUS_VERSION=$(git -C "$PROJECT_ROOT" rev-parse --short HEAD 2>/dev/null || echo 'unknown')

    # Create backup directory
    local backup_dir="$PROJECT_ROOT/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"

    # Backup critical files
    cp -r "$PROJECT_ROOT/app.py" "$backup_dir/" 2>/dev/null || true
    cp -r "$PROJECT_ROOT/templates" "$backup_dir/" 2>/dev/null || true
    cp -r "$PROJECT_ROOT/requirements.txt" "$backup_dir/" 2>/dev/null || true

    local end_time=$(date +%s%3N)
    local duration=$((end_time - start_time))

    log_metric "backup_completed" "{\"backup_path\": \"$backup_dir\", \"previous_version\": \"$PREVIOUS_VERSION\", \"duration_ms\": $duration}"
}

run_health_checks() {
    echo "Running health checks..."

    local attempt=0
    local healthy=false
    local start_time=$(date +%s%3N)

    while [[ $attempt -lt $HEALTH_CHECK_RETRIES ]]; do
        attempt=$((attempt + 1))

        log_metric "health_check_attempt" "{\"attempt\": $attempt, \"max_retries\": $HEALTH_CHECK_RETRIES}"

        local response_code
        response_code=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_CHECK_URL" 2>/dev/null || echo "000")

        if [[ "$response_code" == "200" ]]; then
            healthy=true
            break
        fi

        echo "  Health check attempt $attempt/$HEALTH_CHECK_RETRIES failed (HTTP $response_code)"
        sleep "$HEALTH_CHECK_INTERVAL"
    done

    local end_time=$(date +%s%3N)
    local duration=$((end_time - start_time))

    if [[ "$healthy" == "true" ]]; then
        log_metric "health_check_passed" "{\"attempts\": $attempt, \"duration_ms\": $duration}"
        return 0
    else
        SEVERITY="ERROR" ERROR_CODE="\"HEALTH_CHECK_TIMEOUT\"" \
            log_metric "health_check_failed" "{\"attempts\": $attempt, \"duration_ms\": $duration, \"last_response_code\": \"$response_code\"}"
        SHOULD_ROLLBACK=1
        ROLLBACK_REASON="Health check failed after $attempt attempts"
        return 1
    fi
}

run_smoke_tests() {
    echo "Running smoke tests..."

    local total_latency=0
    local successful_tests=0
    local failed_tests=0
    local latencies=()
    local start_time=$(date +%s%3N)

    for i in $(seq 1 $SMOKE_TEST_ITERATIONS); do
        local test_start=$(date +%s%3N)

        local response_code
        response_code=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_CHECK_URL" 2>/dev/null || echo "000")

        local test_end=$(date +%s%3N)
        local latency=$((test_end - test_start))
        latencies+=($latency)

        if [[ "$response_code" == "200" ]]; then
            successful_tests=$((successful_tests + 1))
            total_latency=$((total_latency + latency))
        else
            failed_tests=$((failed_tests + 1))
        fi

        echo "  Smoke test $i/$SMOKE_TEST_ITERATIONS: HTTP $response_code (${latency}ms)"
    done

    local end_time=$(date +%s%3N)
    local duration=$((end_time - start_time))

    # Calculate average latency
    local avg_latency=0
    if [[ $successful_tests -gt 0 ]]; then
        avg_latency=$((total_latency / successful_tests))
    fi

    # Calculate min/max latency
    local min_latency=${latencies[0]}
    local max_latency=${latencies[0]}
    for lat in "${latencies[@]}"; do
        [[ $lat -lt $min_latency ]] && min_latency=$lat
        [[ $lat -gt $max_latency ]] && max_latency=$lat
    done

    # Convert to seconds for threshold comparison
    local avg_latency_sec=$((avg_latency / 1000))

    log_metric "smoke_test_completed" "{\"total_tests\": $SMOKE_TEST_ITERATIONS, \"successful\": $successful_tests, \"failed\": $failed_tests, \"avg_latency\": $avg_latency_sec, \"avg_latency_ms\": $avg_latency, \"min_latency_ms\": $min_latency, \"max_latency_ms\": $max_latency, \"duration_ms\": $duration}"

    # Check for failures
    if [[ $failed_tests -gt 0 ]]; then
        SEVERITY="ERROR" ERROR_CODE="\"SMOKE_TEST_FAILED\"" \
            log_metric "smoke_test_failure" "{\"failed_count\": $failed_tests}"
        SHOULD_ROLLBACK=1
        ROLLBACK_REASON="Smoke tests failed: $failed_tests out of $SMOKE_TEST_ITERATIONS tests failed"
        return 1
    fi

    # Check latency threshold
    if [[ $avg_latency_sec -gt $LATENCY_THRESHOLD ]]; then
        SEVERITY="WARN" ERROR_CODE="\"HIGH_LATENCY\"" \
            log_metric "latency_threshold_exceeded" "{\"avg_latency\": $avg_latency_sec, \"threshold\": $LATENCY_THRESHOLD}"
        # Don't rollback for high latency, just warn
    fi

    return 0
}

deploy() {
    echo "Deploying version $VERSION to $ENV..."

    local start_time=$(date +%s%3N)

    # Pull latest changes if this is a git-based deployment
    if [[ -d "$PROJECT_ROOT/.git" ]]; then
        git -C "$PROJECT_ROOT" pull origin "$(git -C "$PROJECT_ROOT" rev-parse --abbrev-ref HEAD)" 2>/dev/null || true
    fi

    # Install/update dependencies
    if [[ -f "$PROJECT_ROOT/requirements.txt" ]]; then
        echo "  Installing dependencies..."
        pip install -q -r "$PROJECT_ROOT/requirements.txt" 2>/dev/null || true
    fi

    local end_time=$(date +%s%3N)
    local duration=$((end_time - start_time))

    log_metric "deployment_executed" "{\"duration_ms\": $duration}"
}

rollback() {
    echo "Rolling back to previous version..."

    local start_time=$(date +%s%3N)

    SEVERITY="WARN" \
        log_metric "rollback_started" "{\"reason\": \"$ROLLBACK_REASON\", \"target_version\": \"$PREVIOUS_VERSION\"}"

    send_alert "critical" \
        "Deployment Rollback Triggered" \
        "Reason: $ROLLBACK_REASON\n\nRolling back to version: $PREVIOUS_VERSION"

    # Perform rollback
    if [[ -n "$PREVIOUS_VERSION" && "$PREVIOUS_VERSION" != "unknown" ]]; then
        git -C "$PROJECT_ROOT" checkout "$PREVIOUS_VERSION" 2>/dev/null || true
    fi

    local end_time=$(date +%s%3N)
    local duration=$((end_time - start_time))

    log_metric "rollback_completed" "{\"duration_ms\": $duration, \"rolled_back_to\": \"$PREVIOUS_VERSION\"}"
}

make_decision() {
    local decision
    local reason

    if [[ $SHOULD_ROLLBACK -eq 1 ]]; then
        decision="ROLLBACK_REQUIRED"
        reason="$ROLLBACK_REASON"
    else
        decision="DEPLOYMENT_OK"
        reason="All checks passed"
    fi

    log_metric "deployment_decision" "{\"decision\": \"$decision\", \"reason\": \"$reason\"}"

    echo "$decision"
}

# =============================================================================
# Main Deployment Flow
# =============================================================================

main() {
    ensure_metrics_dir

    echo "=============================================="
    echo "Starting deployment"
    echo "  Deployment ID: $DEPLOYMENT_ID"
    echo "  Environment:   $ENV"
    echo "  Service:       $SERVICE"
    echo "  Version:       $VERSION"
    echo "=============================================="

    # Log deployment start
    log_metric "deployment_started" "{\"target_env\": \"$ENV\", \"target_version\": \"$VERSION\"}"

    send_alert "info" \
        "Deployment Started" \
        "Deploying $SERVICE v$VERSION to $ENV"

    # Step 1: Backup
    backup_current_version

    # Step 2: Deploy
    deploy

    # Step 3: Health checks
    run_health_checks || true

    # Step 4: Smoke tests (only if health checks passed)
    if [[ $SHOULD_ROLLBACK -eq 0 ]]; then
        run_smoke_tests || true
    fi

    # Step 5: Make decision
    local decision
    decision=$(make_decision)

    # Step 6: Execute decision
    if [[ "$decision" == "ROLLBACK_REQUIRED" ]]; then
        rollback
        log_metric "deployment_completed" "{\"status\": \"rolled_back\", \"reason\": \"$ROLLBACK_REASON\"}"

        send_alert "critical" \
            "Deployment Failed - Rolled Back" \
            "Deployment of $SERVICE v$VERSION to $ENV failed and was rolled back.\n\nReason: $ROLLBACK_REASON"

        exit 1
    else
        log_metric "deployment_completed" "{\"status\": \"success\"}"

        send_alert "info" \
            "Deployment Successful" \
            "Successfully deployed $SERVICE v$VERSION to $ENV"

        echo ""
        echo "=============================================="
        echo "Deployment completed successfully!"
        echo "=============================================="
        exit 0
    fi
}

# Run main function
main "$@"
