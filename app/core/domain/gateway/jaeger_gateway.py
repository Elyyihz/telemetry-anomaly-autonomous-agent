from abc import ABC, abstractmethod
from typing import List
from app.core.domain.models.telemetry import TraceSpan


class JaegerGateway(ABC):
    """Abstract interface for inspecting distributed traces in Jaeger."""

    @abstractmethod
    async def get_traces_for_service(
        self,
        service_name: str,
        min_duration_ms: float = 500.0,
        only_errors: bool = True
    ) -> List[TraceSpan]:
        """Fetches slow or errored trace spans to correlate with metric spikes.

        Args:
            service_name: Service name filter.
            min_duration_ms: Minimum latency threshold.
            only_errors: If true, filters for non-2xx spans or error tags.

        Returns:
            List of TraceSpan entities.
        """
        pass
