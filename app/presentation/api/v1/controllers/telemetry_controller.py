import logging
from app.core.usecase.diagnose_infrastructure_usecase import DiagnoseInfrastructureUseCase
from app.presentation.dtos.telemetry_dto import (
    DiagnosisTriggerRequest,
    IncidentDiagnosisResponse,
    MetricAnomalyDto,
    TraceSpanDto,
)
from app.core.domain.enum.anomaly_severity import AnomalySeverity

logger = logging.getLogger("telemetry_agent.presentation.controller")


class TelemetryController:
    """Handles HTTP requests and response mapping for autonomous telemetry diagnostics."""

    def __init__(self, diagnose_use_case: DiagnoseInfrastructureUseCase):
        """Initializes with diagnose use case.

        Args:
            diagnose_use_case: DiagnoseInfrastructureUseCase instance.
        """
        self.diagnose_use_case = diagnose_use_case

    async def trigger_diagnosis(self, req: DiagnosisTriggerRequest) -> IncidentDiagnosisResponse:
        """Executes full autonomous diagnosis.

        Args:
            req: DiagnosisTriggerRequest payload.

        Returns:
            IncidentDiagnosisResponse with root cause analysis.
        """
        logger.info("Step started: API request to diagnose service=%s", req.service_name)

        final_state = await self.diagnose_use_case.execute(
            service_name=req.service_name,
            lookback_minutes=req.lookback_minutes,
            topology_context=req.topology_context,
        )

        anomalies_data = [
            MetricAnomalyDto(
                metric_name=a["metric_name"],
                metric_type=a["metric_type"],
                value=a["value"],
                threshold=a["threshold"],
            )
            for a in final_state.get("anomalies", [])
        ]

        traces_data = [
            TraceSpanDto(
                trace_id=t["trace_id"],
                span_id=t["span_id"],
                service_name=t["service_name"],
                operation_name=t["operation_name"],
                duration_ms=t["duration_ms"],
                status_code=t["status_code"],
                error_message=t.get("error_message"),
            )
            for t in final_state.get("traces", [])
        ]

        diagnosis = final_state.get("diagnosis") or {}
        severity = final_state.get("severity", AnomalySeverity.INFO.value)

        # Presentation user message in pt-BR
        if severity == AnomalySeverity.INFO.value:
            user_msg = f"Infraestrutura do serviço '{req.service_name}' saudável. Nenhuma anomalia detectada."
        else:
            user_msg = f"Atenção: Anomalia de severidade {severity} diagnosticada pelo agente autônomo. Causa raiz identificada."

        logger.info("Step concluded: Responding diagnosis for service=%s", req.service_name)

        return IncidentDiagnosisResponse(
            service_name=req.service_name,
            severity=severity,
            anomalies_detected=len(anomalies_data),
            anomalies=anomalies_data,
            correlated_traces=traces_data,
            root_cause_summary=diagnosis.get("root_cause_summary", "Operação estável."),
            confidence_score=diagnosis.get("confidence_score", 1.0),
            recommended_actions=diagnosis.get("recommended_actions", ["Manter monitoramento contínuo"]),
            auto_remediation=diagnosis.get("auto_remediation_suggested"),
            execution_logs=final_state.get("logs", []),
            user_message=user_msg,
        )
