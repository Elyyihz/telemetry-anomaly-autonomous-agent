import logging
from app.core.domain.gateway.incident_notifier_gateway import IncidentNotifierGateway
from app.core.domain.models.telemetry import AnomalyIncident, RootCauseDiagnosis

logger = logging.getLogger("telemetry_agent.infra.notifier")


class IncidentNotifierGatewayImpl(IncidentNotifierGateway):
    """Logs and dispatches incident diagnostic reports to SRE channels."""

    async def publish_incident_report(
        self,
        incident: AnomalyIncident,
        diagnosis: RootCauseDiagnosis
    ) -> bool:
        """Dispatches structured diagnostic reports.

        Args:
            incident: Incident entity.
            diagnosis: Root cause diagnosis.

        Returns:
            bool indicating delivery success.
        """
        logger.warning(
            "DISPATCHING SRE ALERT: Incident %s on service '%s' (Severity: %s) - Root Cause: %s",
            incident.incident_id,
            incident.service_name,
            incident.severity.value,
            diagnosis.root_cause_summary,
        )
        return True
