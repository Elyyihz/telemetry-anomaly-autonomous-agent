from abc import ABC, abstractmethod
from app.core.domain.models.telemetry import AnomalyIncident, RootCauseDiagnosis


class IncidentNotifierGateway(ABC):
    """Abstract interface for notifying SRE teams and logging incidents."""

    @abstractmethod
    async def publish_incident_report(
        self,
        incident: AnomalyIncident,
        diagnosis: RootCauseDiagnosis
    ) -> bool:
        """Dispatches structured diagnostic reports to notification sinks.

        Args:
            incident: Anomaly incident details.
            diagnosis: Root cause analysis and suggested actions.

        Returns:
            bool indicating delivery success.
        """
        pass
