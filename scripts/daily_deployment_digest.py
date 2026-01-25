#!/usr/bin/env python3
"""
Daily Deployment Digest - Run via cron to send daily summary reports

Sends a comprehensive daily summary of deployment metrics to Slack/Teams.
Designed to be run daily at 9am via cron job.

Usage:
    # Run directly
    python daily_deployment_digest.py

    # With custom API URL
    METRICS_API_URL=http://metrics:8080 python daily_deployment_digest.py

Crontab entry:
    # Send daily digest at 9am
    0 9 * * * /path/to/daily_deployment_digest.py
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests library not available. Install with: pip install requests")


class DailyDigestSender:
    """Generates and sends daily deployment digest."""

    def __init__(
        self,
        metrics_api_url: str = "http://localhost:8080",
        slack_webhook_url: Optional[str] = None,
        teams_webhook_url: Optional[str] = None
    ):
        self.metrics_api_url = metrics_api_url.rstrip('/')
        self.slack_webhook_url = slack_webhook_url
        self.teams_webhook_url = teams_webhook_url

    def fetch_summary(self, days: int = 1) -> Dict[str, Any]:
        """Fetch summary from the metrics API."""
        if not REQUESTS_AVAILABLE:
            return {'error': 'requests library not available'}

        try:
            response = requests.get(
                f'{self.metrics_api_url}/api/summary',
                params={'days': days},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {'error': str(e)}

    def fetch_recent_deployments(self, days: int = 1, limit: int = 10) -> Dict[str, Any]:
        """Fetch recent deployments."""
        if not REQUESTS_AVAILABLE:
            return {'error': 'requests library not available'}

        try:
            response = requests.get(
                f'{self.metrics_api_url}/api/recent',
                params={'days': days, 'limit': limit},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {'error': str(e)}

    def format_slack_digest(self, summary: Dict[str, Any], period_label: str) -> Dict:
        """Format digest for Slack."""
        success_rate = summary.get('success_rate', 0)
        rollback_count = summary.get('rollback_count', 0)
        frequency = summary.get('frequency', {})
        latency = summary.get('latency_stats', {})
        mttr = summary.get('mttr', {})
        recent = summary.get('recent_deployments', [])

        # Determine overall status color
        if success_rate >= 95:
            color = "#00FF00"  # Green
            status_emoji = ""
        elif success_rate >= 80:
            color = "#FFA500"  # Orange
            status_emoji = ""
        else:
            color = "#FF0000"  # Red
            status_emoji = ""

        # Format recent deployments summary
        recent_summary = []
        for dep in recent[:5]:
            status_icon = "" if dep.get('decision') == 'DEPLOYMENT_OK' else ""
            recent_summary.append(
                f"{status_icon} `{dep.get('version', 'N/A')[:10]}` - {dep.get('status', 'unknown')}"
            )
        recent_text = "\n".join(recent_summary) if recent_summary else "No deployments"

        payload = {
            "text": f"{status_emoji} *Daily Deployment Digest - {period_label}*",
            "attachments": [
                {
                    "color": color,
                    "blocks": [
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Success Rate*\n{success_rate}%"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Total Deployments*\n{frequency.get('total', 0)}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Rollbacks*\n{rollback_count}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Avg Latency*\n{latency.get('avg', 0)}s"
                                }
                            ]
                        }
                    ]
                },
                {
                    "color": color,
                    "fields": [
                        {
                            "title": "MTTR (Mean Time To Rollback)",
                            "value": f"{mttr.get('mttr_minutes', 0)} min" if mttr.get('count', 0) > 0 else "N/A (no rollbacks)",
                            "short": True
                        },
                        {
                            "title": "P95 Latency",
                            "value": f"{latency.get('p95', 0)}s",
                            "short": True
                        }
                    ]
                },
                {
                    "color": "#808080",
                    "title": "Recent Deployments",
                    "text": recent_text,
                    "footer": "Deployment Metrics Dashboard",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }

        return payload

    def format_teams_digest(self, summary: Dict[str, Any], period_label: str) -> Dict:
        """Format digest for Microsoft Teams."""
        success_rate = summary.get('success_rate', 0)
        rollback_count = summary.get('rollback_count', 0)
        frequency = summary.get('frequency', {})
        latency = summary.get('latency_stats', {})
        mttr = summary.get('mttr', {})

        # Determine overall status color
        if success_rate >= 95:
            color = "00FF00"
        elif success_rate >= 80:
            color = "FFA500"
        else:
            color = "FF0000"

        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color,
            "summary": f"Daily Deployment Digest - {period_label}",
            "sections": [
                {
                    "activityTitle": f"Daily Deployment Digest - {period_label}",
                    "facts": [
                        {"name": "Success Rate", "value": f"{success_rate}%"},
                        {"name": "Total Deployments", "value": str(frequency.get('total', 0))},
                        {"name": "Rollbacks", "value": str(rollback_count)},
                        {"name": "Avg Latency", "value": f"{latency.get('avg', 0)}s"},
                        {"name": "P95 Latency", "value": f"{latency.get('p95', 0)}s"},
                        {"name": "MTTR", "value": f"{mttr.get('mttr_minutes', 0)} min" if mttr.get('count', 0) > 0 else "N/A"}
                    ],
                    "markdown": True
                }
            ]
        }

        return payload

    def send_slack_digest(self, payload: Dict) -> bool:
        """Send digest to Slack."""
        if not self.slack_webhook_url or not REQUESTS_AVAILABLE:
            return False

        try:
            response = requests.post(self.slack_webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def send_teams_digest(self, payload: Dict) -> bool:
        """Send digest to Microsoft Teams."""
        if not self.teams_webhook_url or not REQUESTS_AVAILABLE:
            return False

        try:
            response = requests.post(self.teams_webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def send_digest(self, days: int = 1) -> Dict[str, Any]:
        """
        Generate and send the daily digest.

        Returns a summary of the operation.
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'period_days': days,
            'slack_sent': False,
            'teams_sent': False,
            'errors': []
        }

        # Calculate period label
        if days == 1:
            yesterday = datetime.now() - timedelta(days=1)
            period_label = yesterday.strftime('%Y-%m-%d')
        else:
            period_label = f"Last {days} days"

        # Fetch summary
        summary = self.fetch_summary(days)

        if 'error' in summary:
            results['errors'].append(f"Failed to fetch summary: {summary['error']}")
            return results

        # Send to Slack
        if self.slack_webhook_url:
            slack_payload = self.format_slack_digest(summary, period_label)
            results['slack_sent'] = self.send_slack_digest(slack_payload)
            if not results['slack_sent']:
                results['errors'].append("Failed to send Slack digest")

        # Send to Teams
        if self.teams_webhook_url:
            teams_payload = self.format_teams_digest(summary, period_label)
            results['teams_sent'] = self.send_teams_digest(teams_payload)
            if not results['teams_sent']:
                results['errors'].append("Failed to send Teams digest")

        return results


def main():
    """Main entry point."""
    # Configuration from environment variables
    metrics_api_url = os.getenv('METRICS_API_URL', 'http://localhost:8080')
    slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    teams_webhook_url = os.getenv('TEAMS_WEBHOOK_URL')
    digest_days = int(os.getenv('DIGEST_DAYS', '1'))

    # Create sender
    sender = DailyDigestSender(
        metrics_api_url=metrics_api_url,
        slack_webhook_url=slack_webhook_url,
        teams_webhook_url=teams_webhook_url
    )

    # Send digest
    results = sender.send_digest(days=digest_days)

    # Print results
    print(f"[{results['timestamp']}] Daily Digest Sent")
    print(f"  Period: {results['period_days']} day(s)")
    print(f"  Slack: {'Sent' if results['slack_sent'] else 'Not sent'}")
    print(f"  Teams: {'Sent' if results['teams_sent'] else 'Not sent'}")

    if results['errors']:
        print("  Errors:")
        for error in results['errors']:
            print(f"    - {error}")
        sys.exit(1)

    if not results['slack_sent'] and not results['teams_sent']:
        print("  Warning: No webhooks configured. Set SLACK_WEBHOOK_URL or TEAMS_WEBHOOK_URL.")

    sys.exit(0)


if __name__ == '__main__':
    main()
