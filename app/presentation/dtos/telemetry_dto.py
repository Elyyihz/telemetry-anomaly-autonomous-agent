from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class DiagnosisTriggerRequest(BaseModel):
    """Payload to trigger an on-demand infrastructure diagnosis."""

    service_name: str = Field(..., example="checkout-service")
    lookback_minutes: int = Field(default=15, ge=1, le=120)
    topology_context: Optional[Dict[str, Any]] = Field(default=None)


class MetricAnomalyDto(BaseModel):
    """DTO representing an observed metric outlier."""

    metric_name: str
    metric_type: str
    value: float
    threshold: float


class TraceSpanDto(BaseModel):
    """DTO representing correlated trace span."""

    trace_id: str
    span_id: str
    service_name: str
    operation_name: str
    duration_ms: float
    status_code: int
    error_message: Optional[str]


class IncidentDiagnosisResponse(BaseModel):
    """Consolidated diagnosis report presented to SREs and users."""

    service_name: str
    severity: str
    anomalies_detected: int
    anomalies: List[MetricAnomalyDto]
    correlated_traces: List[TraceSpanDto]
    root_cause_summary: str
    confidence_score: float
    recommended_actions: List[str]
    auto_remediation: Optional[str]
    execution_logs: List[str]
    user_message: str = Field(..., description="Mensagem contextual direcionada ao usuário final.")
