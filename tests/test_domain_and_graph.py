import pytest
from app.core.domain.models.telemetry import (
    MetricSample,
    TraceSpan,
    AnomalyIncident,
    RootCauseDiagnosis,
)
from app.core.domain.enum.anomaly_severity import AnomalySeverity, MetricType
from app.infrastructure.gateway.prometheus_client_impl import PrometheusGatewayImpl
from app.infrastructure.gateway.jaeger_trace_client_impl import JaegerGatewayImpl
from app.infrastructure.gateway.llama_cpp_client_impl import LlamaCppGatewayImpl
from app.infrastructure.gateway.incident_notifier_impl import IncidentNotifierGatewayImpl
from app.infrastructure.gateway.webhook_remediation_impl import WebhookRemediationGatewayImpl
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
        remediation_gateway=WebhookRemediationGatewayImpl(),
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
    assert result.get("remediation_result") is not None
    assert result["remediation_result"]["status"] == "APPLIED"


@pytest.mark.asyncio
async def test_langgraph_checkpointer_persistence():
    """Validates that LangGraph state survives and is checkpointed per thread."""
    nodes = TelemetryAgentNodes(
        prometheus_gateway=PrometheusGatewayImpl(),
        jaeger_gateway=JaegerGatewayImpl(),
        local_llm_gateway=LlamaCppGatewayImpl(),
        remediation_gateway=WebhookRemediationGatewayImpl(),
    )
    graph_uc = TelemetryAgentGraphUseCase(nodes)
    thread_id = "test-incident-thread-99"

    state = {
        "service_name": "inventory-service",
        "lookback_minutes": 10,
        "metrics": [],
        "anomalies": [],
        "traces": [],
        "topology_context": {"db": "postgres"},
        "diagnosis": None,
        "severity": AnomalySeverity.INFO.value,
        "logs": ["Init"],
        "remediation_result": None,
        "error": None,
    }

    result = await graph_uc.execute(state, thread_id=thread_id)
    assert result["service_name"] == "inventory-service"

    # Verify checkpointer saved state for thread
    snapshot = await graph_uc.workflow.aget_state({"configurable": {"thread_id": thread_id}})
    assert snapshot is not None
    assert snapshot.values["service_name"] == "inventory-service"


def test_structured_slack_and_discord_payload_formatting():
    """Validates generation of Slack Block Kit and Discord Embed cards."""
    notifier = IncidentNotifierGatewayImpl()

    incident = AnomalyIncident(
        service_name="payment-gateway",
        severity=AnomalySeverity.CRITICAL,
    )
    diagnosis = RootCauseDiagnosis(
        incident_id=incident.incident_id,
        root_cause_summary="Connection pool exhaustion in RDS primary instance",
        confidence_score=0.96,
        recommended_actions=["Increase max connections", "Restart stale idle workers"],
        auto_remediation_suggested="RESTART_POD",
    )

    slack_card = notifier.build_slack_payload(incident, diagnosis)
    assert "blocks" in slack_card
    assert any("CRITICAL" in str(b) for b in slack_card["blocks"])
    assert any("Connection pool exhaustion" in str(b) for b in slack_card["blocks"])

    discord_card = notifier.build_discord_payload(incident, diagnosis)
    assert "embeds" in discord_card
    assert discord_card["embeds"][0]["color"] == 15158332
    assert "Connection pool exhaustion" in discord_card["embeds"][0]["description"]
