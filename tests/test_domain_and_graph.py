import pytest
from app.core.domain.models.telemetry import MetricSample, TraceSpan, AnomalyIncident
from app.core.domain.enum.anomaly_severity import AnomalySeverity, MetricType
from app.infrastructure.gateway.prometheus_client_impl import PrometheusGatewayImpl
from app.infrastructure.gateway.jaeger_trace_client_impl import JaegerGatewayImpl
from app.infrastructure.gateway.llama_cpp_client_impl import LlamaCppGatewayImpl
from app.infrastructure.gateway.incident_notifier_impl import IncidentNotifierGatewayImpl
from app.core.usecase.anomaly_agent.nodes import TelemetryAgentNodes
from app.core.usecase.anomaly_agent.graph import TelemetryAgentGraphUseCase
from app.core.usecase.diagnose_infrastructure_usecase import DiagnoseInfrastructureUseCase


def test_domain_model_creation():
    """Validates metric sample entity creation."""
    metric = MetricSample(
        service_name="payment-service",
        metric_name="p99_latency",
        metric_type=MetricType.LATENCY_P99,
        value=720.0,
        threshold=400.0,
        is_anomalous=True,
    )
    assert metric.is_anomalous is True
    assert metric.value == 720.0


@pytest.mark.asyncio
async def test_agent_graph_execution():
    """Tests full agentic LangGraph workflow diagnosing simulated infrastructure anomalies."""
    nodes = TelemetryAgentNodes(
        prometheus_gateway=PrometheusGatewayImpl(),
        jaeger_gateway=JaegerGatewayImpl(),
        local_llm_gateway=LlamaCppGatewayImpl(),
    )
    graph_uc = TelemetryAgentGraphUseCase(nodes)
    diag_uc = DiagnoseInfrastructureUseCase(graph_uc, IncidentNotifierGatewayImpl())

    result = await diag_uc.execute("order-checkout-service")

    assert result["service_name"] == "order-checkout-service"
    assert len(result["anomalies"]) > 0
    assert len(result["traces"]) > 0
    assert result["diagnosis"] is not None
    assert result["diagnosis"]["confidence_score"] > 0.8
    assert len(result["diagnosis"]["recommended_actions"]) > 0
