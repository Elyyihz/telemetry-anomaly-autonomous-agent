from abc import ABC, abstractmethod
from typing import List
from app.core.domain.models.telemetry import MetricSample


class PrometheusGateway(ABC):
    """Abstract interface for querying Prometheus time-series metrics."""

    @abstractmethod
    async def query_service_metrics(self, service_name: str, lookback_minutes: int = 15) -> List[MetricSample]:
        """Queries telemetry metrics for latency, error rate, CPU and memory.

        Args:
            service_name: Name of target service.
            lookback_minutes: Window size for metrics query.

        Returns:
            List of MetricSample instances.
        """
        pass
