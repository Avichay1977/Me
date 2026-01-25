#!/usr/bin/env python3
"""
Deployment Metrics Analyzer & API Server

A production-grade SRE tool for analyzing deployment metrics, detecting anomalies,
and providing RESTful API endpoints for dashboard integration.

Usage:
    # CLI mode:
    python analyze_deployment_metrics.py /path/to/metrics.jsonl --days 30

    # API Server mode:
    python analyze_deployment_metrics.py /path/to/metrics.jsonl --server --port 8080
"""

import argparse
import json
import os
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from flask import Flask, jsonify, request
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class DeploymentMetricsAnalyzer:
    """Analyzes deployment metrics from JSONL files."""

    def __init__(self, metrics_file: str):
        self.metrics_file = Path(metrics_file)
        self.metrics: List[Dict[str, Any]] = []
        self._load_metrics()

    def _load_metrics(self) -> None:
        """Load metrics from JSONL file."""
        if not self.metrics_file.exists():
            return

        with open(self.metrics_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        self.metrics.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

    def reload_metrics(self) -> None:
        """Reload metrics from file (useful for API server)."""
        self.metrics = []
        self._load_metrics()

    def filter_by_timerange(self, days: int) -> List[Dict[str, Any]]:
        """Filter metrics to last N days."""
        cutoff = datetime.now() - timedelta(days=days)

        filtered = []
        for m in self.metrics:
            try:
                ts = m.get('timestamp', '')
                # Handle various timestamp formats
                if ts.endswith('Z'):
                    ts = ts[:-1] + '+00:00'
                metric_time = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                if metric_time.replace(tzinfo=None) >= cutoff:
                    filtered.append(m)
            except (ValueError, TypeError):
                continue

        return filtered

    def get_success_rate(self, days: int = 30) -> float:
        """Calculate deployment success rate."""
        recent = self.filter_by_timerange(days)
        decisions = [m for m in recent if m.get('event') == 'deployment_decision']

        if not decisions:
            return 100.0

        successful = sum(1 for d in decisions
                        if d.get('data', {}).get('decision') == 'DEPLOYMENT_OK')

        return round((successful / len(decisions)) * 100, 2)

    def get_rollback_count(self, days: int = 30) -> int:
        """Count rollbacks in the given time period."""
        recent = self.filter_by_timerange(days)
        return sum(1 for m in recent if m.get('event') == 'rollback_completed')

    def get_latency_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get latency statistics from smoke tests."""
        recent = self.filter_by_timerange(days)
        smoke_tests = [m for m in recent if m.get('event') == 'smoke_test_completed']

        latencies = []
        for st in smoke_tests:
            data = st.get('data', {})
            lat = data.get('avg_latency') or data.get('avg_latency_ms', 0) / 1000
            if lat:
                latencies.append(lat)

        if not latencies:
            return {'avg': 0, 'min': 0, 'max': 0, 'p50': 0, 'p95': 0, 'p99': 0}

        latencies_sorted = sorted(latencies)
        n = len(latencies_sorted)

        return {
            'avg': round(statistics.mean(latencies), 3),
            'min': round(min(latencies), 3),
            'max': round(max(latencies), 3),
            'p50': round(latencies_sorted[int(n * 0.5)], 3),
            'p95': round(latencies_sorted[int(n * 0.95)] if n > 1 else latencies_sorted[-1], 3),
            'p99': round(latencies_sorted[int(n * 0.99)] if n > 1 else latencies_sorted[-1], 3),
            'count': n
        }

    def get_mttr(self, days: int = 30) -> Dict[str, Any]:
        """Calculate Mean Time To Rollback."""
        recent = self.filter_by_timerange(days)

        rollbacks = []
        for m in recent:
            if m.get('event') == 'rollback_completed':
                dep_id = m.get('deployment_id')

                # Find the deployment_started event for this deployment
                start = next((x for x in recent
                             if x.get('deployment_id') == dep_id
                             and x.get('event') == 'deployment_started'), None)

                if start:
                    try:
                        start_ts = start['timestamp'].replace('Z', '+00:00')
                        rollback_ts = m['timestamp'].replace('Z', '+00:00')

                        start_time = datetime.fromisoformat(start_ts)
                        rollback_time = datetime.fromisoformat(rollback_ts)

                        duration_min = (rollback_time - start_time).total_seconds() / 60
                        rollbacks.append({
                            'deployment_id': dep_id,
                            'duration_minutes': duration_min,
                            'start_time': start['timestamp'],
                            'rollback_time': m['timestamp']
                        })
                    except (ValueError, KeyError):
                        continue

        if not rollbacks:
            return {
                'count': 0,
                'mttr_minutes': 0,
                'max_minutes': 0,
                'min_minutes': 0,
                'rollbacks': []
            }

        durations = [r['duration_minutes'] for r in rollbacks]

        return {
            'count': len(rollbacks),
            'mttr_minutes': round(sum(durations) / len(durations), 2),
            'max_minutes': round(max(durations), 2),
            'min_minutes': round(min(durations), 2),
            'rollbacks': rollbacks
        }

    def get_anomalies(self, days: int = 30, std_threshold: float = 2.0) -> List[Dict]:
        """Detect deployment anomalies (latency outliers)."""
        recent = self.filter_by_timerange(days)
        smoke_tests = [m for m in recent if m.get('event') == 'smoke_test_completed']

        latencies = []
        for st in smoke_tests:
            data = st.get('data', {})
            lat = data.get('avg_latency') or data.get('avg_latency_ms', 0) / 1000
            if lat:
                latencies.append(lat)

        if len(latencies) < 3:
            return []

        mean = statistics.mean(latencies)
        stdev = statistics.stdev(latencies)

        if stdev == 0:
            return []

        anomalies = []
        for st in smoke_tests:
            data = st.get('data', {})
            lat = data.get('avg_latency') or data.get('avg_latency_ms', 0) / 1000
            if not lat:
                continue

            if abs(lat - mean) > std_threshold * stdev:
                anomalies.append({
                    'deployment_id': st.get('deployment_id'),
                    'timestamp': st.get('timestamp'),
                    'latency': lat,
                    'mean': round(mean, 3),
                    'stdev': round(stdev, 3),
                    'deviation_from_mean': round(lat - mean, 3),
                    'z_score': round((lat - mean) / stdev, 2),
                    'severity': 'high' if abs(lat - mean) > 3 * stdev else 'medium'
                })

        return anomalies

    def get_deployment_frequency(self, days: int = 30) -> Dict[str, Any]:
        """Get deployment frequency statistics."""
        recent = self.filter_by_timerange(days)
        starts = [m for m in recent if m.get('event') == 'deployment_started']

        # Group by date
        by_date = defaultdict(int)
        by_hour = defaultdict(int)
        by_weekday = defaultdict(int)

        for s in starts:
            try:
                ts = s['timestamp'].replace('Z', '+00:00')
                dt = datetime.fromisoformat(ts)
                date = dt.strftime('%Y-%m-%d')
                hour = dt.strftime('%H')
                weekday = dt.strftime('%A')

                by_date[date] += 1
                by_hour[hour] += 1
                by_weekday[weekday] += 1
            except (ValueError, KeyError):
                continue

        return {
            'total': len(starts),
            'per_day_avg': round(len(starts) / max(days, 1), 2),
            'by_date': dict(sorted(by_date.items())),
            'by_hour': dict(sorted(by_hour.items())),
            'by_weekday': dict(by_weekday)
        }

    def get_recent_deployments(self, days: int = 7, limit: int = 10) -> List[Dict]:
        """Get list of recent deployments with their outcomes."""
        recent = self.filter_by_timerange(days)

        # Group by deployment_id
        deployments = defaultdict(list)
        for m in recent:
            dep_id = m.get('deployment_id')
            if dep_id:
                deployments[dep_id].append(m)

        results = []
        for dep_id, events in deployments.items():
            # Extract key information
            started = next((e for e in events if e.get('event') == 'deployment_started'), None)
            completed = next((e for e in events if e.get('event') == 'deployment_completed'), None)
            decision = next((e for e in events if e.get('event') == 'deployment_decision'), None)
            smoke_test = next((e for e in events if e.get('event') == 'smoke_test_completed'), None)

            if started:
                results.append({
                    'deployment_id': dep_id,
                    'timestamp': started.get('timestamp'),
                    'version': started.get('version'),
                    'env': started.get('env'),
                    'service': started.get('service'),
                    'triggered_by': started.get('triggered_by'),
                    'user': started.get('user'),
                    'decision': decision.get('data', {}).get('decision') if decision else None,
                    'status': completed.get('data', {}).get('status') if completed else 'in_progress',
                    'latency': smoke_test.get('data', {}).get('avg_latency') if smoke_test else None
                })

        # Sort by timestamp descending
        results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return results[:limit]

    def compare_deployments(self, id1: str, id2: str) -> Dict[str, Any]:
        """Compare two deployments."""
        dep1_events = [m for m in self.metrics if m.get('deployment_id') == id1]
        dep2_events = [m for m in self.metrics if m.get('deployment_id') == id2]

        def extract_metrics(events: List[Dict]) -> Dict[str, Any]:
            if not events:
                return {'found': False}

            smoke = next((e for e in events if e.get('event') == 'smoke_test_completed'), None)
            decision = next((e for e in events if e.get('event') == 'deployment_decision'), None)
            started = next((e for e in events if e.get('event') == 'deployment_started'), None)
            completed = next((e for e in events if e.get('event') == 'deployment_completed'), None)

            return {
                'found': True,
                'version': events[0].get('version'),
                'env': events[0].get('env'),
                'timestamp': started.get('timestamp') if started else None,
                'latency': smoke.get('data', {}).get('avg_latency') if smoke else None,
                'decision': decision.get('data', {}).get('decision') if decision else None,
                'status': completed.get('data', {}).get('status') if completed else None,
                'event_count': len(events)
            }

        m1 = extract_metrics(dep1_events)
        m2 = extract_metrics(dep2_events)

        latency_delta = None
        if m1.get('latency') is not None and m2.get('latency') is not None:
            latency_delta = round(m1['latency'] - m2['latency'], 3)

        return {
            'deployment_1': m1,
            'deployment_2': m2,
            'diff': {
                'latency_delta': latency_delta
            }
        }

    def get_health_timeline(self, deployment_id: str) -> Dict[str, Any]:
        """Get all health check events for a deployment."""
        events = [m for m in self.metrics
                 if m.get('deployment_id') == deployment_id
                 and 'health' in m.get('event', '').lower()]

        return {
            'deployment_id': deployment_id,
            'health_checks': [{
                'timestamp': e['timestamp'],
                'event': e['event'],
                'elapsed_ms': e.get('elapsed_from_start_ms'),
                'data': e.get('data')
            } for e in events]
        }

    def evaluate_alerts(self, days: int = 7) -> Dict[str, Any]:
        """Check if any alerts should fire."""
        alerts = []

        # Alert 1: Success rate drop
        success_rate = self.get_success_rate(days)
        if success_rate < 80:
            alerts.append({
                'severity': 'high',
                'alert': 'LOW_SUCCESS_RATE',
                'message': f'Success rate dropped to {success_rate:.1f}% (last {days}d)',
                'value': success_rate,
                'threshold': 80
            })

        # Alert 2: High latency
        latency = self.get_latency_stats(days)
        if latency['avg'] > 20:
            alerts.append({
                'severity': 'medium',
                'alert': 'HIGH_LATENCY',
                'message': f'Avg latency: {latency["avg"]}s exceeds 20s',
                'value': latency['avg'],
                'threshold': 20
            })

        # Alert 3: Multiple recent rollbacks
        rollback_count = self.get_rollback_count(days)
        if rollback_count >= 3:
            alerts.append({
                'severity': 'critical',
                'alert': 'FREQUENT_ROLLBACKS',
                'message': f'{rollback_count} rollbacks in {days} days',
                'value': rollback_count,
                'threshold': 3
            })

        # Alert 4: Anomalies detected
        anomalies = self.get_anomalies(days)
        high_severity_anomalies = [a for a in anomalies if a['severity'] == 'high']
        if high_severity_anomalies:
            alerts.append({
                'severity': 'medium',
                'alert': 'ANOMALIES_DETECTED',
                'message': f'{len(high_severity_anomalies)} high-severity anomalies detected',
                'value': len(high_severity_anomalies),
                'threshold': 0
            })

        overall_status = 'ok'
        if any(a['severity'] == 'critical' for a in alerts):
            overall_status = 'critical'
        elif any(a['severity'] == 'high' for a in alerts):
            overall_status = 'warning'
        elif alerts:
            overall_status = 'info'

        return {
            'active_alerts': len(alerts),
            'alerts': alerts,
            'status': overall_status,
            'evaluated_at': datetime.now().isoformat()
        }

    def get_trends(self, metric: str = 'success_rate', days: int = 30) -> Dict[str, Any]:
        """Get trends over time (grouped by week)."""
        recent = self.filter_by_timerange(days)
        decisions = [m for m in recent if m.get('event') == 'deployment_decision']

        # Group by week
        by_week = defaultdict(list)
        for d in decisions:
            try:
                ts = d['timestamp'].replace('Z', '+00:00')
                dt = datetime.fromisoformat(ts)
                week = dt.strftime('%Y-W%W')
                success = d.get('data', {}).get('decision') == 'DEPLOYMENT_OK'
                by_week[week].append(success)
            except (ValueError, KeyError):
                continue

        trend = []
        for week, vals in sorted(by_week.items()):
            trend.append({
                'period': week,
                'success_rate': round(sum(vals) / len(vals) * 100, 2),
                'total': len(vals),
                'successful': sum(vals)
            })

        direction = 'stable'
        if len(trend) >= 2:
            if trend[-1]['success_rate'] > trend[0]['success_rate']:
                direction = 'improving'
            elif trend[-1]['success_rate'] < trend[0]['success_rate']:
                direction = 'declining'

        return {
            'metric': metric,
            'trend': trend,
            'direction': direction,
            'period_days': days
        }

    def get_version_stats(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get success rate by version."""
        recent = self.filter_by_timerange(days)
        decisions = [m for m in recent if m.get('event') == 'deployment_decision']

        by_version = defaultdict(list)
        for d in decisions:
            version = d.get('version', 'unknown')
            success = d.get('data', {}).get('decision') == 'DEPLOYMENT_OK'
            by_version[version].append(success)

        results = []
        for version, vals in by_version.items():
            results.append({
                'version': version,
                'total': len(vals),
                'successful': sum(vals),
                'success_rate': round(sum(vals) / len(vals) * 100, 2) if vals else 0
            })

        return sorted(results, key=lambda x: x['success_rate'], reverse=True)

    def get_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get a comprehensive summary of deployment metrics."""
        return {
            'period_days': days,
            'generated_at': datetime.now().isoformat(),
            'success_rate': self.get_success_rate(days),
            'rollback_count': self.get_rollback_count(days),
            'latency_stats': self.get_latency_stats(days),
            'mttr': self.get_mttr(days),
            'frequency': self.get_deployment_frequency(days),
            'recent_deployments': self.get_recent_deployments(days),
            'alerts': self.evaluate_alerts(min(days, 7)),
            'trends': self.get_trends('success_rate', days)
        }


# =============================================================================
# Flask API Server
# =============================================================================

def create_app(metrics_file: str) -> 'Flask':
    """Create Flask application with API endpoints."""
    if not FLASK_AVAILABLE:
        raise ImportError("Flask is required for API server. Install with: pip install flask")

    app = Flask(__name__)
    analyzer = DeploymentMetricsAnalyzer(metrics_file)

    @app.before_request
    def reload_metrics():
        """Reload metrics on each request to get fresh data."""
        analyzer.reload_metrics()

    @app.route('/')
    def index():
        """API documentation."""
        return jsonify({
            'name': 'Deployment Metrics API',
            'version': '1.0.0',
            'endpoints': {
                '/api/summary': 'GET - Comprehensive metrics summary',
                '/api/success_rate': 'GET - Deployment success rate',
                '/api/latency': 'GET - Latency statistics',
                '/api/mttr': 'GET - Mean Time To Rollback',
                '/api/deployment_frequency': 'GET - Deployment frequency stats',
                '/api/recent': 'GET - Recent deployments',
                '/api/anomalies': 'GET - Detect anomalous deployments',
                '/api/compare': 'GET - Compare two deployments',
                '/api/health_timeline/<deployment_id>': 'GET - Health check timeline',
                '/api/alerts/evaluate': 'GET - Evaluate alert conditions',
                '/api/trends': 'GET - Success rate trends',
                '/api/versions': 'GET - Success rate by version'
            }
        })

    @app.route('/api/summary')
    def api_summary():
        """Get comprehensive metrics summary."""
        days = int(request.args.get('days', 30))
        return jsonify(analyzer.get_summary(days))

    @app.route('/api/success_rate')
    def api_success_rate():
        """Get deployment success rate."""
        days = int(request.args.get('days', 30))
        return jsonify({
            'success_rate': analyzer.get_success_rate(days),
            'period_days': days
        })

    @app.route('/api/latency')
    def api_latency():
        """Get latency statistics."""
        days = int(request.args.get('days', 30))
        stats = analyzer.get_latency_stats(days)
        stats['period_days'] = days
        return jsonify(stats)

    @app.route('/api/mttr')
    def api_mttr():
        """Get Mean Time To Rollback."""
        days = int(request.args.get('days', 30))
        result = analyzer.get_mttr(days)
        result['period_days'] = days
        return jsonify(result)

    @app.route('/api/deployment_frequency')
    def api_frequency():
        """Get deployment frequency statistics."""
        days = int(request.args.get('days', 30))
        result = analyzer.get_deployment_frequency(days)
        result['period_days'] = days
        return jsonify(result)

    @app.route('/api/recent')
    def api_recent():
        """Get recent deployments."""
        days = int(request.args.get('days', 7))
        limit = int(request.args.get('limit', 10))
        return jsonify({
            'deployments': analyzer.get_recent_deployments(days, limit),
            'period_days': days
        })

    @app.route('/api/anomalies')
    def api_anomalies():
        """Detect anomalous deployments."""
        days = int(request.args.get('days', 30))
        threshold = float(request.args.get('std_threshold', 2.0))
        return jsonify({
            'anomalies': analyzer.get_anomalies(days, threshold),
            'std_threshold': threshold,
            'period_days': days
        })

    @app.route('/api/compare')
    def api_compare():
        """Compare two deployments."""
        id1 = request.args.get('deployment_id1')
        id2 = request.args.get('deployment_id2')

        if not id1 or not id2:
            return jsonify({'error': 'Both deployment_id1 and deployment_id2 are required'}), 400

        return jsonify(analyzer.compare_deployments(id1, id2))

    @app.route('/api/health_timeline/<deployment_id>')
    def api_health_timeline(deployment_id: str):
        """Get health check timeline for a deployment."""
        return jsonify(analyzer.get_health_timeline(deployment_id))

    @app.route('/api/alerts/evaluate')
    def api_evaluate_alerts():
        """Evaluate alert conditions."""
        days = int(request.args.get('days', 7))
        return jsonify(analyzer.evaluate_alerts(days))

    @app.route('/api/trends')
    def api_trends():
        """Get success rate trends."""
        metric = request.args.get('metric', 'success_rate')
        days = int(request.args.get('days', 30))
        return jsonify(analyzer.get_trends(metric, days))

    @app.route('/api/versions')
    def api_versions():
        """Get success rate by version."""
        days = int(request.args.get('days', 30))
        return jsonify({
            'versions': analyzer.get_version_stats(days),
            'period_days': days
        })

    return app


# =============================================================================
# Alert Sending Functions
# =============================================================================

def send_anomaly_alert(anomaly: Dict, webhook_url: str) -> None:
    """Send alert for detected anomaly."""
    if not REQUESTS_AVAILABLE:
        print("Warning: requests library not available for sending alerts")
        return

    severity_emoji = "" if anomaly['severity'] == 'high' else ""

    payload = {
        "text": f"{severity_emoji} *Deployment Anomaly Detected*",
        "attachments": [{
            "color": "#FF6B6B" if anomaly['severity'] == 'high' else "#FFA500",
            "fields": [
                {"title": "Deployment ID", "value": anomaly['deployment_id'], "short": True},
                {"title": "Timestamp", "value": anomaly['timestamp'], "short": True},
                {"title": "Latency", "value": f"{anomaly['latency']}s", "short": True},
                {"title": "Deviation", "value": f"+{anomaly['deviation_from_mean']}s from mean", "short": True}
            ],
            "footer": "Deployment Metrics Analyzer"
        }]
    }

    try:
        requests.post(webhook_url, json=payload, timeout=5)
    except Exception as e:
        print(f"Failed to send alert: {e}")


# =============================================================================
# CLI Interface
# =============================================================================

def print_cli_report(analyzer: DeploymentMetricsAnalyzer, days: int, output_json: bool = False) -> None:
    """Print CLI report."""
    summary = analyzer.get_summary(days)

    if output_json:
        print(json.dumps(summary, indent=2))
        return

    print("=" * 60)
    print(f"DEPLOYMENT METRICS REPORT (Last {days} days)")
    print("=" * 60)
    print()

    print(f"Success Rate:    {summary['success_rate']}%")
    print(f"Rollback Count:  {summary['rollback_count']}")
    print()

    print("Latency Statistics:")
    lat = summary['latency_stats']
    print(f"  Average: {lat['avg']}s  |  Min: {lat['min']}s  |  Max: {lat['max']}s")
    print(f"  P50: {lat['p50']}s  |  P95: {lat['p95']}s  |  P99: {lat['p99']}s")
    print()

    mttr = summary['mttr']
    if mttr['count'] > 0:
        print("MTTR (Mean Time To Rollback):")
        print(f"  Average: {mttr['mttr_minutes']} min  |  Min: {mttr['min_minutes']} min  |  Max: {mttr['max_minutes']} min")
        print()

    freq = summary['frequency']
    print("Deployment Frequency:")
    print(f"  Total: {freq['total']}  |  Per Day (avg): {freq['per_day_avg']}")
    print()

    alerts = summary['alerts']
    if alerts['alerts']:
        print(f"ALERTS ({alerts['status'].upper()}):")
        for alert in alerts['alerts']:
            print(f"  [{alert['severity'].upper()}] {alert['alert']}: {alert['message']}")
        print()

    print("Recent Deployments:")
    for dep in summary['recent_deployments'][:5]:
        status = dep.get('decision') or dep.get('status') or 'unknown'
        print(f"  {dep['deployment_id'][:20]:20} | {dep.get('version', 'N/A'):10} | {status}")

    print()
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Analyze deployment metrics from JSONL files'
    )
    parser.add_argument('metrics_file', help='Path to metrics JSONL file')
    parser.add_argument('--days', type=int, default=30, help='Number of days to analyze')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    parser.add_argument('--server', action='store_true', help='Start API server')
    parser.add_argument('--port', type=int, default=8080, help='API server port')
    parser.add_argument('--host', default='0.0.0.0', help='API server host')

    args = parser.parse_args()

    if not Path(args.metrics_file).exists():
        print(f"Warning: Metrics file not found: {args.metrics_file}")
        print("Creating empty metrics file...")
        Path(args.metrics_file).parent.mkdir(parents=True, exist_ok=True)
        Path(args.metrics_file).touch()

    if args.server:
        if not FLASK_AVAILABLE:
            print("Error: Flask is required for API server. Install with: pip install flask")
            sys.exit(1)

        app = create_app(args.metrics_file)
        print(f"Starting API server on http://{args.host}:{args.port}")
        app.run(host=args.host, port=args.port, debug=False)
    else:
        analyzer = DeploymentMetricsAnalyzer(args.metrics_file)
        print_cli_report(analyzer, args.days, args.json)


if __name__ == '__main__':
    main()
