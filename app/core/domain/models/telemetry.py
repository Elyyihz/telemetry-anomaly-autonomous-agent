from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import uuid

from app.core.domain.enum.anomaly_severity import AnomalySeverity, MetricType


@dataclass
class MetricSample:
    """Individual time-series data point retrieved from Prometheus.

    Attributes:
        service_name: Originating service or pod identifier.
        metric_name: Label or PromQL query key.
        metric_type: Standardized MetricType classification.
        value: Numeric measurement (e.g. ms, percentage, error count).
        threshold: Standard baseline expected value.
        is_anomalous: Boolean flag set by Z-score or threshold evaluator.
        timestamp: Time of observation.
    """

    service_name: str
    metric_name: str
    metric_type: MetricType
    value: float
    threshold: float
    is_anomalous: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class TraceSpan:
    """Distributed tracing span retrieved from Jaeger.

    Attributes:
        trace_id: Global distributed trace ID.
        span_id: Specific operation span ID.
        service_name: Microservice generating the span.
        operation_name: HTTP endpoint or database query name.
        duration_ms: Latency of span in milliseconds.
        status_code: HTTP response code or gRPC status.
        error_message: Optional exception stack trace or error log.
    """

    trace_id: str
    span_id: str
    service_name: str
    operation_name: str
    duration_ms: float
    status_code: int = 200
    error_message: Optional[str] = None


@dataclass
class AnomalyIncident:
    """Identified operational incident requiring autonomous agent investigation.

    Attributes:
        incident_id: Unique incident identifier.
        service_name: Impacted service.
        severity: Assessed criticality.
        detected_metrics: Set of anomalous MetricSample records.
        correlated_traces: Subset of slow or failing trace spans.
        detected_at: Timestamp of initial alert.
    """

    incident_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    service_name: str = ""
    severity: AnomalySeverity = AnomalySeverity.LOW
    detected_metrics: List[MetricSample] = field(default_factory=list)
    correlated_traces: List[TraceSpan] = field(default_factory=list)
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RootCauseDiagnosis:
    """LLM agent synthesized explanation and prescriptive remediation.

    Attributes:
        diagnosis_id: UUID of diagnosis session.
        incident_id: Linked incident UUID.
        root_cause_summary: Technical summary of why failure occurred.
        confidence_score: Model confidence in diagnosis [0.0 - 1.0].
        recommended_actions: Prescriptive steps for engineer/SRE team.
        auto_remediation_suggested: Recommended automation hook (e.g. restart, scale).
        completed_at: Synthesis completion timestamp.
    """

    diagnosis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    incident_id: str = ""
    root_cause_summary: str = ""
    confidence_score: float = 0.0
    recommended_actions: List[str] = field(default_factory=list)
    auto_remediation_suggested: Optional[str] = None
    completed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
