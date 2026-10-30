from typing import TypedDict, Optional, Dict, Any, List


class TelemetryAgentState(TypedDict):
    """LangGraph agent state tracking the telemetry diagnostic workflow.

    Attributes:
        service_name: Target microservice name.
        lookback_minutes: Time window queried in Prometheus.
        metrics: Retrieved MetricSample records.
        anomalies: Filtered anomalous metric samples.
        traces: Retrieved correlated Jaeger distributed trace spans.
        topology_context: Dependencies (e.g. database, cache, external endpoints).
        diagnosis: Synthesized RootCauseDiagnosis by llama.cpp.
        severity: Consolidated AnomalySeverity rating.
        logs: Diagnostic step traces.
        error: Failure message if execution fails.
    """

    service_name: str
    lookback_minutes: int
    metrics: List[Dict[str, Any]]
    anomalies: List[Dict[str, Any]]
    traces: List[Dict[str, Any]]
    topology_context: Dict[str, Any]
    diagnosis: Optional[Dict[str, Any]]
    severity: str
    logs: List[str]
    error: Optional[str]
