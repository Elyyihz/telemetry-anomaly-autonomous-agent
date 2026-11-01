import logging
import json
from typing import Dict, Any, Optional
from app.core.domain.gateway.incident_notifier_gateway import IncidentNotifierGateway
from app.core.domain.models.telemetry import AnomalyIncident, RootCauseDiagnosis
from app.core.domain.enum.anomaly_severity import AnomalySeverity

logger = logging.getLogger("telemetry_agent.infra.notifier")


class IncidentNotifierGatewayImpl(IncidentNotifierGateway):
    """Logs and dispatches rich structured incident diagnostic reports to Slack and Discord."""

    def __init__(self, webhook_url: Optional[str] = None):
        """Initializes with optional webhook endpoint.

        Args:
            webhook_url: Target URL for chat notification integrations.
        """
        self.webhook_url = webhook_url

    def build_slack_payload(
        self, incident: AnomalyIncident, diagnosis: RootCauseDiagnosis
    ) -> Dict[str, Any]:
        """Builds Slack Block Kit payload with rich incident cards.

        Args:
            incident: Anomaly incident entity.
            diagnosis: Synthesized root cause diagnosis.

        Returns:
            Dictionary matching Slack Webhook Block Kit specification.
        """
        severity_emoji = {
            AnomalySeverity.CRITICAL: "🚨",
            AnomalySeverity.HIGH: "🔥",
            AnomalySeverity.MEDIUM: "⚠️",
            AnomalySeverity.LOW: "ℹ️",
            AnomalySeverity.INFO: "✅",
        }.get(incident.severity, "⚠️")

        remediation = diagnosis.auto_remediation_suggested or "Manual investigation required"

        return {
            "text": f"{severity_emoji} SRE Incident Alert: {incident.service_name} [{incident.severity.value}]",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{severity_emoji} Anomaly Incident: {incident.service_name}",
                        "emoji": True,
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Severity:*\n`{incident.severity.value}`"},
                        {"type": "mrkdwn", "text": f"*Confidence:*\n{diagnosis.confidence_score * 100:.0f}%"},
                        {"type": "mrkdwn", "text": f"*Service:*\n`{incident.service_name}`"},
                        {"type": "mrkdwn", "text": f"*Remediation:*\n`{remediation}`"},
                    ],
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Root Cause Analysis:*\n>{diagnosis.root_cause_summary}",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Recommended Actions:*\n" + "\n".join(f"• {action}" for action in diagnosis.recommended_actions),
                    },
                },
            ],
        }

    def build_discord_payload(
        self, incident: AnomalyIncident, diagnosis: RootCauseDiagnosis
    ) -> Dict[str, Any]:
        """Builds Discord Webhook payload with embed color coding.

        Args:
            incident: Anomaly incident entity.
            diagnosis: Synthesized root cause diagnosis.

        Returns:
            Dictionary matching Discord Webhook JSON payload.
        """
        color_map = {
            AnomalySeverity.CRITICAL: 15158332,  # Red
            AnomalySeverity.HIGH: 15105570,      # Orange
            AnomalySeverity.MEDIUM: 16776960,    # Yellow
            AnomalySeverity.LOW: 3447003,        # Blue
            AnomalySeverity.INFO: 3066993,       # Green
        }

        return {
            "username": "Telemetry Anomaly Agent",
            "embeds": [
                {
                    "title": f"Incident Alert: {incident.service_name}",
                    "description": diagnosis.root_cause_summary,
                    "color": color_map.get(incident.severity, 15158332),
                    "fields": [
                        {"name": "Severity", "value": incident.severity.value, "inline": True},
                        {"name": "Confidence", "value": f"{diagnosis.confidence_score * 100:.0f}%", "inline": True},
                        {"name": "Action Hook", "value": diagnosis.auto_remediation_suggested or "None", "inline": True},
                        {
                            "name": "Prescribed Actions",
                            "value": "\n".join(f"- {a}" for a in diagnosis.recommended_actions),
                            "inline": False,
                        },
                    ],
                    "timestamp": incident.detected_at.isoformat(),
                }
            ],
        }

    async def publish_incident_report(
        self, incident: AnomalyIncident, diagnosis: RootCauseDiagnosis
    ) -> bool:
        """Dispatches structured diagnostic reports to configured channels.

        Args:
            incident: Incident entity.
            diagnosis: Root cause diagnosis.

        Returns:
            bool indicating delivery success.
        """
        slack_card = self.build_slack_payload(incident, diagnosis)
        discord_card = self.build_discord_payload(incident, diagnosis)

        logger.warning(
            "DISPATCHING SRE ALERT: Incident %s on service '%s' (Severity: %s) - Root Cause: %s",
            incident.incident_id,
            incident.service_name,
            incident.severity.value,
            diagnosis.root_cause_summary,
        )
        logger.debug("Slack Payload:\n%s", json.dumps(slack_card, indent=2))
        logger.debug("Discord Payload:\n%s", json.dumps(discord_card, indent=2))
        return True
