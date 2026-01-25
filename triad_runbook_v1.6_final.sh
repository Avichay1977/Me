#!/usr/bin/env bash
#
# Triad Environment Setup Runbook v1.6
# For: Cubase Script Assistant
#
# This script sets up the complete Triad stack:
#   - Flask Application
#   - Prometheus (Metrics)
#   - Grafana (Visualization)
#   - Loki + Promtail (Logging)
#

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
METRICS_FILE="${SCRIPT_DIR}/deployment_metrics.jsonl"
LOG_DIR="${SCRIPT_DIR}/logs"
MONITORING_DIR="${SCRIPT_DIR}/monitoring"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# Helper Functions
# =============================================================================
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_metric() {
    local event_type="$1"
    local status="$2"
    local details="${3:-}"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "{\"timestamp\":\"${timestamp}\",\"event\":\"${event_type}\",\"status\":\"${status}\",\"details\":\"${details}\"}" >> "${METRICS_FILE}"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is not installed. Please install it first."
        return 1
    fi
    return 0
}

# =============================================================================
# Pre-flight Checks
# =============================================================================
preflight_checks() {
    log_info "Running pre-flight checks..."

    local failed=0

    # Check Docker
    if ! check_command docker; then
        failed=1
    else
        if ! docker info &> /dev/null; then
            log_error "Docker daemon is not running"
            failed=1
        fi
    fi

    # Check Docker Compose
    if ! check_command docker-compose && ! docker compose version &> /dev/null; then
        log_error "docker-compose or docker compose is not available"
        failed=1
    fi

    # Check for .env file
    if [[ ! -f "${SCRIPT_DIR}/.env" ]]; then
        log_warning ".env file not found. Creating template..."
        echo "GOOGLE_API_KEY=your_api_key_here" > "${SCRIPT_DIR}/.env"
        log_warning "Please update .env with your actual API key"
    fi

    if [[ $failed -eq 1 ]]; then
        log_error "Pre-flight checks failed"
        log_metric "preflight" "failed" "Missing dependencies"
        return 1
    fi

    log_success "Pre-flight checks passed"
    log_metric "preflight" "success"
    return 0
}

# =============================================================================
# Setup Monitoring Configuration
# =============================================================================
setup_monitoring_config() {
    log_info "Setting up monitoring configuration..."

    # Create directories
    mkdir -p "${MONITORING_DIR}/prometheus"
    mkdir -p "${MONITORING_DIR}/grafana/provisioning/datasources"
    mkdir -p "${MONITORING_DIR}/grafana/provisioning/dashboards"
    mkdir -p "${MONITORING_DIR}/loki"
    mkdir -p "${MONITORING_DIR}/promtail"
    mkdir -p "${LOG_DIR}"

    # Prometheus configuration
    cat > "${MONITORING_DIR}/prometheus/prometheus.yml" << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'cubase-assistant'
    static_configs:
      - targets: ['cubase-assistant:5001']
    metrics_path: /metrics
    scrape_interval: 10s

  - job_name: 'docker'
    static_configs:
      - targets: ['host.docker.internal:9323']
EOF

    # Grafana datasources
    cat > "${MONITORING_DIR}/grafana/provisioning/datasources/datasources.yml" << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: false
EOF

    # Grafana dashboards provisioning
    cat > "${MONITORING_DIR}/grafana/provisioning/dashboards/dashboards.yml" << 'EOF'
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: 'Triad'
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

    # Loki configuration
    cat > "${MONITORING_DIR}/loki/loki-config.yml" << 'EOF'
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  instance_addr: 127.0.0.1
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

query_range:
  results_cache:
    cache:
      embedded_cache:
        enabled: true
        max_size_mb: 100

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

ruler:
  alertmanager_url: http://localhost:9093

limits_config:
  reject_old_samples: true
  reject_old_samples_max_age: 168h
EOF

    # Promtail configuration
    cat > "${MONITORING_DIR}/promtail/promtail-config.yml" << 'EOF'
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: app-logs
    static_configs:
      - targets:
          - localhost
        labels:
          job: cubase-assistant
          __path__: /var/log/app/*.log

  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: 'container'
EOF

    log_success "Monitoring configuration created"
    log_metric "monitoring_config" "success"
}

# =============================================================================
# Build and Start Services
# =============================================================================
build_services() {
    log_info "Building Docker images..."

    cd "${SCRIPT_DIR}"

    if docker compose version &> /dev/null; then
        docker compose build --no-cache
    else
        docker-compose build --no-cache
    fi

    log_success "Docker images built"
    log_metric "build" "success"
}

start_services() {
    log_info "Starting Triad stack..."

    cd "${SCRIPT_DIR}"

    if docker compose version &> /dev/null; then
        docker compose up -d
    else
        docker-compose up -d
    fi

    log_success "Services started"
    log_metric "start" "success"
}

stop_services() {
    log_info "Stopping Triad stack..."

    cd "${SCRIPT_DIR}"

    if docker compose version &> /dev/null; then
        docker compose down
    else
        docker-compose down
    fi

    log_success "Services stopped"
    log_metric "stop" "success"
}

# =============================================================================
# Health Checks
# =============================================================================
wait_for_service() {
    local service_name="$1"
    local url="$2"
    local max_attempts="${3:-30}"
    local attempt=1

    log_info "Waiting for ${service_name}..."

    while [[ $attempt -le $max_attempts ]]; do
        if curl -sf "${url}" > /dev/null 2>&1; then
            log_success "${service_name} is ready"
            return 0
        fi
        sleep 2
        ((attempt++))
    done

    log_error "${service_name} failed to start within timeout"
    return 1
}

health_check() {
    log_info "Running health checks..."

    local all_healthy=0

    # Check Flask App
    if ! wait_for_service "Cubase Assistant" "http://localhost:5001" 30; then
        all_healthy=1
    fi

    # Check Prometheus
    if ! wait_for_service "Prometheus" "http://localhost:9090/-/ready" 30; then
        all_healthy=1
    fi

    # Check Grafana
    if ! wait_for_service "Grafana" "http://localhost:3000/api/health" 30; then
        all_healthy=1
    fi

    # Check Loki
    if ! wait_for_service "Loki" "http://localhost:3100/ready" 30; then
        all_healthy=1
    fi

    if [[ $all_healthy -eq 0 ]]; then
        log_success "All services are healthy"
        log_metric "health_check" "success"
    else
        log_error "Some services are unhealthy"
        log_metric "health_check" "failed"
    fi

    return $all_healthy
}

# =============================================================================
# Status and Logs
# =============================================================================
show_status() {
    log_info "Service Status:"
    echo ""

    if docker compose version &> /dev/null; then
        docker compose ps
    else
        docker-compose ps
    fi

    echo ""
    log_info "Service URLs:"
    echo "  - Cubase Assistant: http://localhost:5001"
    echo "  - Prometheus:       http://localhost:9090"
    echo "  - Grafana:          http://localhost:3000 (admin/triad_admin)"
    echo "  - Loki:             http://localhost:3100"
}

show_logs() {
    local service="${1:-}"

    if [[ -n "$service" ]]; then
        if docker compose version &> /dev/null; then
            docker compose logs -f "$service"
        else
            docker-compose logs -f "$service"
        fi
    else
        if docker compose version &> /dev/null; then
            docker compose logs -f
        else
            docker-compose logs -f
        fi
    fi
}

# =============================================================================
# Cleanup
# =============================================================================
cleanup() {
    log_info "Cleaning up Triad stack..."

    cd "${SCRIPT_DIR}"

    if docker compose version &> /dev/null; then
        docker compose down -v --remove-orphans
    else
        docker-compose down -v --remove-orphans
    fi

    log_success "Cleanup complete"
    log_metric "cleanup" "success"
}

# =============================================================================
# Main
# =============================================================================
print_usage() {
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  setup     - Run full setup (config + build + start + health check)"
    echo "  start     - Start all services"
    echo "  stop      - Stop all services"
    echo "  restart   - Restart all services"
    echo "  build     - Build Docker images"
    echo "  status    - Show service status"
    echo "  logs      - Show logs (optional: service name)"
    echo "  health    - Run health checks"
    echo "  cleanup   - Stop and remove all containers, volumes"
    echo ""
}

main() {
    local command="${1:-}"

    case "$command" in
        setup)
            log_info "Starting Triad Environment Setup v1.6"
            echo ""
            preflight_checks || exit 1
            setup_monitoring_config
            build_services
            start_services
            sleep 5
            health_check
            echo ""
            show_status
            log_metric "setup_complete" "success"
            ;;
        start)
            start_services
            sleep 3
            health_check
            show_status
            ;;
        stop)
            stop_services
            ;;
        restart)
            stop_services
            sleep 2
            start_services
            sleep 5
            health_check
            show_status
            ;;
        build)
            build_services
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "${2:-}"
            ;;
        health)
            health_check
            ;;
        cleanup)
            cleanup
            ;;
        *)
            print_usage
            exit 1
            ;;
    esac
}

main "$@"
