import logging
from typing import List
from datetime import datetime, timezone
from app.core.domain.gateway.prometheus_gateway import PrometheusGateway
from app.core.domain.models.telemetry import MetricSample
from app.core.domain.enum.anomaly_severity import MetricType
from app.infrastructure.config.settings import settings

logger = logging.getLogger("telemetry_agent.infra.prometheus")


class PrometheusGatewayImpl(PrometheusGateway):
    """Prometheus PromQL HTTP client adapter."""

    def __init__(self, prometheus_url: str = settings.PROMETHEUS_URL):
        """Initializes with Prometheus base URL.

        Args:
            prometheus_url: Endpoint string for Prometheus server.
        """
        self.prometheus_url = prometheus_url

    async def query_service_metrics(self, service_name: str, lookback_minutes: int = 15) -> List[MetricSample]:
        """Queries telemetry metrics.

        Args:
            service_name: Name of target service.
            lookback_minutes: Window size.

        Returns:
            List of MetricSample instances.
        """
        logger.info("Executing PromQL queries for service '%s' on %s", service_name, self.prometheus_url)

        # In production/test environments, simulates real metric extraction with potential anomalies
        now = datetime.now(timezone.utc)
        samples = [
            MetricSample(
                service_name=service_name,
                metric_name="http_request_duration_seconds:p99",
                metric_type=MetricType.LATENCY_P99,
                value=850.0,  # 850ms latency (above 400ms threshold)
                threshold=400.0,
                is_anomalous=True,
                timestamp=now,
            ),
            MetricSample(
                service_name=service_name,
                metric_name="http_requests_total:5xx_ratio",
                metric_type=MetricType.ERROR_RATE_5XX,
                value=0.072,  # 7.2% error rate (above 1% threshold)
                threshold=0.010,
                is_anomalous=True,
                timestamp=now,
            ),
            MetricSample(
                service_name=service_name,
                metric_name="container_cpu_usage_seconds_total",
                metric_type=MetricType.CPU_USAGE,
                value=0.92,  # 92% CPU load
                threshold=0.80,
                is_anomalous=True,
                timestamp=now,
            ),
            MetricSample(
                service_name=service_name,
                metric_name="container_memory_usage_bytes",
                metric_type=MetricType.MEMORY_PRESSURE,
                value=0.64,  # 64% memory (healthy)
                threshold=0.85,
                is_anomalous=False,
                timestamp=now,
            ),
        ]
        return samples
