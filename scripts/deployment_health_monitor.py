#!/usr/bin/env python3
"""
Deployment Health Monitor - Run via cron for continuous monitoring

This script checks sliding window metrics and alerts on degradation.
Designed to be run hourly via cron job.

Usage:
    # Run directly
    python deployment_health_monitor.py

    # With custom API URL
    METRICS_API_URL=http://metrics:8080 python deployment_health_monitor.py

Crontab entry:
    # Check deployment health every hour
    0 * * * * /path/to/deployment_health_monitor.py
"""

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests library not available. Install with: pip install requests")


class DeploymentHealthMonitor:
    """Monitors deployment health and sends alerts."""

    def __init__(
        self,
        metrics_api_url: str = "http://localhost:8080",
        slack_webhook_url: Optional[str] = None,
        teams_webhook_url: Optional[str] = None,
        pagerduty_routing_key: Optional[str] = None
    ):
        self.metrics_api_url = metrics_api_url.rstrip('/')
        self.slack_webhook_url = slack_webhook_url
        self.teams_webhook_url = teams_webhook_url
        self.pagerduty_routing_key = pagerduty_routing_key

    def fetch_alerts(self, days: int = 7) -> Dict[str, Any]:
        """Fetch alerts from the metrics API."""
        if not REQUESTS_AVAILABLE:
            return {'error': 'requests library not available', 'alerts': []}

        try:
            response = requests.get(
                f'{self.metrics_api_url}/api/alerts/evaluate',
                params={'days': days},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {'error': str(e), 'alerts': []}

    def fetch_anomalies(self, days: int = 7) -> Dict[str, Any]:
        """Fetch anomalies from the metrics API."""
        if not REQUESTS_AVAILABLE:
            return {'error': 'requests library not available', 'anomalies': []}

        try:
            response = requests.get(
                f'{self.metrics_api_url}/api/anomalies',
                params={'days': days, 'std_threshold': 2.0},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {'error': str(e), 'anomalies': []}

    def send_slack_alert(self, alert: Dict[str, Any]) -> bool:
        """Send alert to Slack."""
        if not self.slack_webhook_url or not REQUESTS_AVAILABLE:
            return False

        severity_config = {
            'critical': {'emoji': '', 'color': '#FF0000'},
            'high': {'emoji': '', 'color': '#FF6B6B'},
            'medium': {'emoji': '', 'color': '#FFA500'},
            'low': {'emoji': '', 'color': '#FFFF00'},
            'info': {'emoji': '', 'color': '#00FF00'}
        }

        config = severity_config.get(alert.get('severity', 'info'), severity_config['info'])

        payload = {
            "text": f"{config['emoji']} *{alert.get('alert', 'ALERT')}*",
            "attachments": [{
                "color": config['color'],
                "fields": [
                    {"title": "Message", "value": alert.get('message', 'No message'), "short": False},
                    {"title": "Current Value", "value": str(alert.get('value', 'N/A')), "short": True},
                    {"title": "Threshold", "value": str(alert.get('threshold', 'N/A')), "short": True},
                    {"title": "Severity", "value": alert.get('severity', 'unknown').upper(), "short": True},
                    {"title": "Time", "value": datetime.now().isoformat(), "short": True}
                ],
                "footer": "Deployment Health Monitor",
                "ts": int(datetime.now().timestamp())
            }]
        }

        try:
            response = requests.post(self.slack_webhook_url, json=payload, timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def send_teams_alert(self, alert: Dict[str, Any]) -> bool:
        """Send alert to Microsoft Teams."""
        if not self.teams_webhook_url or not REQUESTS_AVAILABLE:
            return False

        severity_colors = {
            'critical': 'FF0000',
            'high': 'FF6B6B',
            'medium': 'FFA500',
            'low': 'FFFF00',
            'info': '00FF00'
        }

        color = severity_colors.get(alert.get('severity', 'info'), '808080')

        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color,
            "summary": alert.get('alert', 'Deployment Alert'),
            "sections": [{
                "activityTitle": f"Deployment Alert: {alert.get('alert', 'ALERT')}",
                "facts": [
                    {"name": "Message", "value": alert.get('message', 'No message')},
                    {"name": "Current Value", "value": str(alert.get('value', 'N/A'))},
                    {"name": "Threshold", "value": str(alert.get('threshold', 'N/A'))},
                    {"name": "Severity", "value": alert.get('severity', 'unknown').upper()},
                    {"name": "Time", "value": datetime.now().isoformat()}
                ],
                "markdown": True
            }]
        }

        try:
            response = requests.post(self.teams_webhook_url, json=payload, timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def send_pagerduty_alert(self, alert: Dict[str, Any]) -> bool:
        """Send alert to PagerDuty."""
        if not self.pagerduty_routing_key or not REQUESTS_AVAILABLE:
            return False

        severity_map = {
            'critical': 'critical',
            'high': 'error',
            'medium': 'warning',
            'low': 'info',
            'info': 'info'
        }

        payload = {
            "routing_key": self.pagerduty_routing_key,
            "event_action": "trigger",
            "payload": {
                "summary": f"{alert.get('alert', 'ALERT')}: {alert.get('message', 'No message')}",
                "severity": severity_map.get(alert.get('severity', 'info'), 'info'),
                "source": "deployment-health-monitor",
                "custom_details": {
                    "value": alert.get('value'),
                    "threshold": alert.get('threshold'),
                    "severity": alert.get('severity')
                }
            }
        }

        try:
            response = requests.post(
                'https://events.pagerduty.com/v2/enqueue',
                json=payload,
                timeout=5
            )
            return response.status_code == 202
        except requests.RequestException:
            return False

    def send_anomaly_alert(self, anomaly: Dict[str, Any]) -> bool:
        """Send anomaly detection alert."""
        alert = {
            'alert': 'ANOMALY_DETECTED',
            'severity': anomaly.get('severity', 'medium'),
            'message': f"Deployment {anomaly.get('deployment_id', 'unknown')[:12]} has anomalous latency: {anomaly.get('latency', 'N/A')}s (z-score: {anomaly.get('z_score', 'N/A')})",
            'value': anomaly.get('latency'),
            'threshold': f"mean + {anomaly.get('z_score', 2)} std"
        }
        return self.send_slack_alert(alert)

    def check_health(self, days: int = 7) -> Dict[str, Any]:
        """
        Main health check routine.

        Returns a summary of the health check results.
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'alerts_fetched': 0,
            'alerts_sent': 0,
            'anomalies_fetched': 0,
            'anomalies_sent': 0,
            'errors': []
        }

        # Check alerts
        alerts_data = self.fetch_alerts(days)

        if 'error' in alerts_data:
            results['errors'].append(f"Failed to fetch alerts: {alerts_data['error']}")
        else:
            alerts = alerts_data.get('alerts', [])
            results['alerts_fetched'] = len(alerts)

            for alert in alerts:
                sent = False
                if self.slack_webhook_url:
                    sent = self.send_slack_alert(alert) or sent
                if self.teams_webhook_url:
                    sent = self.send_teams_alert(alert) or sent
                if self.pagerduty_routing_key and alert.get('severity') in ['critical', 'high']:
                    sent = self.send_pagerduty_alert(alert) or sent

                if sent:
                    results['alerts_sent'] += 1

        # Check anomalies
        anomalies_data = self.fetch_anomalies(days)

        if 'error' in anomalies_data:
            results['errors'].append(f"Failed to fetch anomalies: {anomalies_data['error']}")
        else:
            anomalies = anomalies_data.get('anomalies', [])
            # Only alert on high severity anomalies
            high_severity = [a for a in anomalies if a.get('severity') == 'high']
            results['anomalies_fetched'] = len(high_severity)

            for anomaly in high_severity:
                if self.send_anomaly_alert(anomaly):
                    results['anomalies_sent'] += 1

        return results


def main():
    """Main entry point."""
    # Configuration from environment variables
    metrics_api_url = os.getenv('METRICS_API_URL', 'http://localhost:8080')
    slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    teams_webhook_url = os.getenv('TEAMS_WEBHOOK_URL')
    pagerduty_routing_key = os.getenv('PAGERDUTY_ROUTING_KEY')
    check_days = int(os.getenv('CHECK_DAYS', '7'))

    # Create monitor
    monitor = DeploymentHealthMonitor(
        metrics_api_url=metrics_api_url,
        slack_webhook_url=slack_webhook_url,
        teams_webhook_url=teams_webhook_url,
        pagerduty_routing_key=pagerduty_routing_key
    )

    # Run health check
    results = monitor.check_health(days=check_days)

    # Print results
    print(f"[{results['timestamp']}] Health Check Complete")
    print(f"  Alerts: {results['alerts_fetched']} fetched, {results['alerts_sent']} sent")
    print(f"  Anomalies: {results['anomalies_fetched']} fetched, {results['anomalies_sent']} sent")

    if results['errors']:
        print("  Errors:")
        for error in results['errors']:
            print(f"    - {error}")
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
