import logging
from typing import Dict, Any, List, Optional
from app.core.domain.gateway.prometheus_gateway import PrometheusGateway
from app.core.domain.gateway.jaeger_gateway import JaegerGateway
from app.core.domain.gateway.local_llm_gateway import LocalLlmGateway
from app.core.domain.gateway.remediation_gateway import RemediationGateway
from app.core.domain.models.telemetry import MetricSample, TraceSpan, MetricType
from app.core.domain.enum.anomaly_severity import AnomalySeverity
from app.core.usecase.anomaly_agent.state import TelemetryAgentState

logger = logging.getLogger("telemetry_agent.nodes")


class TelemetryAgentNodes:
    """Action nodes for the autonomous telemetry diagnosis LangGraph workflow."""

    def __init__(
        self,
        prometheus_gateway: PrometheusGateway,
        jaeger_gateway: JaegerGateway,
        local_llm_gateway: LocalLlmGateway,
        remediation_gateway: Optional[RemediationGateway] = None,
    ):
        """Initializes nodes with telemetry and LLM dependencies.

        Args:
            prometheus_gateway: Prometheus adapter.
            jaeger_gateway: Jaeger tracing adapter.
            local_llm_gateway: llama.cpp adapter.
            remediation_gateway: Optional self-healing remediation adapter.
        """
        self.prometheus_gateway = prometheus_gateway
        self.jaeger_gateway = jaeger_gateway
        self.local_llm_gateway = local_llm_gateway
        self.remediation_gateway = remediation_gateway

    async def node_fetch_metrics(self, state: TelemetryAgentState) -> Dict[str, Any]:
        """Queries Prometheus for time-series metrics over observation window.

        Args:
            state: Current agent state.

        Returns:
            Updated state dictionary with raw metrics.
        """
        svc = state["service_name"]
        logger.info("Step started: Fetching telemetry metrics from Prometheus for service=%s", svc)

        samples = await self.prometheus_gateway.query_service_metrics(
            service_name=svc,
            lookback_minutes=state.get("lookback_minutes", 15),
        )

        metrics_data = [
            {
                "service_name": s.service_name,
                "metric_name": s.metric_name,
                "metric_type": s.metric_type.value,
                "value": s.value,
                "threshold": s.threshold,
                "is_anomalous": s.is_anomalous,
            }
            for s in samples
        ]

        logger.info("Decision taken: Retrieved %d metric samples from Prometheus for service=%s", len(metrics_data), svc)
        logger.info("Step concluded: Metrics query completed for service=%s", svc)

        return {
            "metrics": metrics_data,
            "logs": state["logs"] + [f"Fetched {len(metrics_data)} metrics from Prometheus"],
        }

    async def node_evaluate_anomalies(self, state: TelemetryAgentState) -> Dict[str, Any]:
        """Filters metrics that exceed operational thresholds.

        Args:
            state: Current agent state.

        Returns:
            Updated state dictionary with filtered anomalies and assigned severity.
        """
        svc = state["service_name"]
        logger.info("Step started: Evaluating statistical thresholds and anomaly flags for service=%s", svc)

        raw_metrics = state.get("metrics", [])
        anomalies = [m for m in raw_metrics if m["is_anomalous"] or m["value"] > m["threshold"]]

        if not anomalies:
            logger.info("Decision taken: No anomalies detected; infrastructure operating within normal baseline")
            severity = AnomalySeverity.INFO.value
        else:
            # Determine severity based on metric types
            has_5xx = any(a["metric_type"] == MetricType.ERROR_RATE_5XX.value for a in anomalies)
            has_latency = any(a["metric_type"] == MetricType.LATENCY_P99.value for a in anomalies)

            if has_5xx and has_latency:
                severity = AnomalySeverity.CRITICAL.value
            elif has_5xx:
                severity = AnomalySeverity.HIGH.value
            elif has_latency:
                severity = AnomalySeverity.MEDIUM.value
            else:
                severity = AnomalySeverity.LOW.value

            logger.warning(
                "Decision taken: Detected %d anomalies; classified incident as severity=%s",
                len(anomalies),
                severity,
            )

        logger.info("Step concluded: Anomaly evaluation finished for service=%s", svc)
        return {
            "anomalies": anomalies,
            "severity": severity,
            "logs": state["logs"] + [f"Evaluated {len(anomalies)} anomalies, severity: {severity}"],
        }

    async def node_fetch_correlated_traces(self, state: TelemetryAgentState) -> Dict[str, Any]:
        """Fetches spans from Jaeger that correlate with identified metric spikes.

        Args:
            state: Current agent state.

        Returns:
            Updated state dictionary with matching trace spans.
        """
        svc = state["service_name"]
        logger.info("Step started: Fetching correlated distributed traces from Jaeger for service=%s", svc)

        spans = await self.jaeger_gateway.get_traces_for_service(
            service_name=svc,
            min_duration_ms=400.0,
            only_errors=True,
        )

        traces_data = [
            {
                "trace_id": t.trace_id,
                "span_id": t.span_id,
                "service_name": t.service_name,
                "operation_name": t.operation_name,
                "duration_ms": t.duration_ms,
                "status_code": t.status_code,
                "error_message": t.error_message,
            }
            for t in spans
        ]

        logger.info("Decision taken: Correlated %d trace spans with operational incident", len(traces_data))
        logger.info("Step concluded: Trace inspection concluded for service=%s", svc)

        return {
            "traces": traces_data,
            "logs": state["logs"] + [f"Correlated {len(traces_data)} trace spans from Jaeger"],
        }

    async def node_diagnose_root_cause_llm(self, state: TelemetryAgentState) -> Dict[str, Any]:
        """Invokes local llama.cpp GGUF model to synthesize root cause and prescribe fixes.

        Args:
            state: Current agent state.

        Returns:
            Updated state dictionary containing root cause diagnosis and recommendations.
        """
        svc = state["service_name"]
        logger.info("Step started: Generating root cause diagnosis via local llama.cpp for service=%s", svc)

        # Convert back to domain models for gateway
        domain_anomalies = [
            MetricSample(
                service_name=a["service_name"],
                metric_name=a["metric_name"],
                metric_type=MetricType(a["metric_type"]),
                value=a["value"],
                threshold=a["threshold"],
                is_anomalous=True,
            )
            for a in state.get("anomalies", [])
        ]

        domain_traces = [
            TraceSpan(
                trace_id=t["trace_id"],
                span_id=t["span_id"],
                service_name=t["service_name"],
                operation_name=t["operation_name"],
                duration_ms=t["duration_ms"],
                status_code=t["status_code"],
                error_message=t.get("error_message"),
            )
            for t in state.get("traces", [])
        ]

        diagnosis = await self.local_llm_gateway.diagnose_incident(
            service_name=svc,
            anomalies=domain_anomalies,
            traces=domain_traces,
            topology_context=state.get("topology_context", {}),
        )

        diagnosis_data = {
            "diagnosis_id": diagnosis.diagnosis_id,
            "incident_id": diagnosis.incident_id,
            "root_cause_summary": diagnosis.root_cause_summary,
            "confidence_score": diagnosis.confidence_score,
            "recommended_actions": diagnosis.recommended_actions,
            "auto_remediation_suggested": diagnosis.auto_remediation_suggested,
        }

        logger.info(
            "Decision taken: llama.cpp synthesized diagnosis with confidence=%.2f: %s",
            diagnosis.confidence_score,
            diagnosis.root_cause_summary,
        )
        logger.info("Step concluded: Root cause diagnosis concluded for service=%s", svc)

        return {
            "diagnosis": diagnosis_data,
            "logs": state["logs"] + [f"Diagnosis synthesized: {diagnosis.root_cause_summary[:60]}..."],
        }

    async def node_auto_remediate(self, state: TelemetryAgentState) -> Dict[str, Any]:
        """Dispatches self-healing remediation actions if prescribed by the diagnosis.

        Args:
            state: Current agent state.

        Returns:
            Updated state with remediation outcome.
        """
        diag = state.get("diagnosis")
        remediation_action = diag.get("auto_remediation_suggested") if diag else None

        if not remediation_action or not self.remediation_gateway:
            logger.info("Decision taken: No automated remediation needed or gateway unavailable")
            return {
                "remediation_result": None,
                "logs": state["logs"] + ["No automated remediation performed"],
            }

        logger.info("Step started: Executing self-healing action '%s'", remediation_action)
        outcome = await self.remediation_gateway.execute_remediation(
            action=remediation_action,
            service_name=state["service_name"],
            parameters={"diagnosis_id": diag.get("diagnosis_id")},
        )
        logger.info(
            "Step concluded: Self-healing action '%s' completed with status=%s",
            remediation_action,
            outcome.get("status"),
        )

        return {
            "remediation_result": outcome,
            "logs": state["logs"] + [f"Self-healing applied: {remediation_action}"],
        }
