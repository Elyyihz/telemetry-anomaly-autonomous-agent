import logging
from typing import Dict, Any, Optional
from app.core.domain.models.telemetry import AnomalyIncident, RootCauseDiagnosis
from app.core.domain.enum.anomaly_severity import AnomalySeverity
from app.core.domain.gateway.incident_notifier_gateway import IncidentNotifierGateway
from app.core.usecase.anomaly_agent.graph import TelemetryAgentGraphUseCase
from app.core.usecase.anomaly_agent.state import TelemetryAgentState

logger = logging.getLogger("telemetry_agent.usecase.diagnose")


class DiagnoseInfrastructureUseCase:
    """Application use case initiating agentic telemetry diagnostics."""

    def __init__(
        self,
        graph_use_case: TelemetryAgentGraphUseCase,
        notifier_gateway: IncidentNotifierGateway,
    ):
        """Initializes use case with LangGraph workflow and notifier gateway.

        Args:
            graph_use_case: TelemetryAgentGraphUseCase instance.
            notifier_gateway: IncidentNotifierGateway port.
        """
        self.graph_use_case = graph_use_case
        self.notifier_gateway = notifier_gateway

    async def execute(
        self,
        service_name: str,
        lookback_minutes: int = 15,
        topology_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Runs autonomous diagnostic agent on service infrastructure.

        Args:
            service_name: Name of monitored service.
            lookback_minutes: Window of metrics.
            topology_context: Architecture dependency context.

        Returns:
            Dict containing incident summary, severity, and diagnosis.
        """
        logger.info("Step started: Initiating autonomous diagnostic scan for service=%s", service_name)

        initial_state: TelemetryAgentState = {
            "service_name": service_name,
            "lookback_minutes": lookback_minutes,
            "metrics": [],
            "anomalies": [],
            "traces": [],
            "topology_context": topology_context or {"database": "postgresql", "cache": "redis"},
            "diagnosis": None,
            "severity": AnomalySeverity.INFO.value,
            "logs": ["Diagnostic agent initiated"],
            "error": None,
        }

        final_state = await self.graph_use_case.execute(initial_state)

        # If anomalies were found and diagnosed, notify SRE sink
        if final_state.get("diagnosis"):
            incident = AnomalyIncident(
                service_name=service_name,
                severity=AnomalySeverity(final_state.get("severity", AnomalySeverity.LOW.value)),
            )
            diag_dict = final_state["diagnosis"]
            diagnosis = RootCauseDiagnosis(
                incident_id=incident.incident_id,
                root_cause_summary=diag_dict["root_cause_summary"],
                confidence_score=diag_dict["confidence_score"],
                recommended_actions=diag_dict["recommended_actions"],
                auto_remediation_suggested=diag_dict.get("auto_remediation_suggested"),
            )
            await self.notifier_gateway.publish_incident_report(incident, diagnosis)

        logger.info("Step concluded: Diagnostic scan completed for service=%s with severity=%s", service_name, final_state.get("severity"))
        return final_state
