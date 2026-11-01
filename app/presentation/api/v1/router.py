from fastapi import APIRouter, Depends
from app.presentation.dtos.telemetry_dto import DiagnosisTriggerRequest, IncidentDiagnosisResponse
from app.presentation.api.v1.controllers.telemetry_controller import TelemetryController
from app.infrastructure.gateway.prometheus_client_impl import PrometheusGatewayImpl
from app.infrastructure.gateway.jaeger_trace_client_impl import JaegerGatewayImpl
from app.infrastructure.gateway.llama_cpp_client_impl import LlamaCppGatewayImpl
from app.infrastructure.gateway.incident_notifier_impl import IncidentNotifierGatewayImpl
from app.infrastructure.gateway.webhook_remediation_impl import WebhookRemediationGatewayImpl
from app.core.usecase.anomaly_agent.nodes import TelemetryAgentNodes
from app.core.usecase.anomaly_agent.graph import TelemetryAgentGraphUseCase
from app.core.usecase.diagnose_infrastructure_usecase import DiagnoseInfrastructureUseCase

router = APIRouter(prefix="/api/v1", tags=["Autonomous Telemetry Agent"])


def get_telemetry_controller() -> TelemetryController:
    """Dependency injection factory for telemetry controller."""
    prom_gw = PrometheusGatewayImpl()
    jaeger_gw = JaegerGatewayImpl()
    llm_gw = LlamaCppGatewayImpl()
    notifier_gw = IncidentNotifierGatewayImpl()
    remediation_gw = WebhookRemediationGatewayImpl()

    nodes = TelemetryAgentNodes(
        prometheus_gateway=prom_gw,
        jaeger_gateway=jaeger_gw,
        local_llm_gateway=llm_gw,
        remediation_gateway=remediation_gw,
    )
    graph_uc = TelemetryAgentGraphUseCase(nodes)
    diag_uc = DiagnoseInfrastructureUseCase(graph_uc, notifier_gw)
    return TelemetryController(diag_uc)


@router.post("/diagnose", response_model=IncidentDiagnosisResponse)
async def trigger_diagnosis(
    req: DiagnosisTriggerRequest,
    controller: TelemetryController = Depends(get_telemetry_controller),
) -> IncidentDiagnosisResponse:
    """Triggers LangGraph agent to consume Prometheus metrics & Jaeger traces and generate root-cause diagnoses."""
    return await controller.trigger_diagnosis(req)


@router.get("/health")
def health_check():
    """Readiness probe."""
    return {"status": "UP", "service": "telemetry-anomaly-autonomous-agent"}
