from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.core.domain.models.telemetry import MetricSample, TraceSpan, RootCauseDiagnosis


class LocalLlmGateway(ABC):
    """Abstract interface for local llama.cpp GGUF inference."""

    @abstractmethod
    async def diagnose_incident(
        self,
        service_name: str,
        anomalies: List[MetricSample],
        traces: List[TraceSpan],
        topology_context: Dict[str, Any]
    ) -> RootCauseDiagnosis:
        """Executes LLM reasoning to diagnose root cause and suggest remediation.

        Args:
            service_name: Service experiencing anomaly.
            anomalies: Detected metric spikes.
            traces: Associated distributed spans.
            topology_context: Dependencies and architecture metadata.

        Returns:
            RootCauseDiagnosis domain entity.
        """
        pass
