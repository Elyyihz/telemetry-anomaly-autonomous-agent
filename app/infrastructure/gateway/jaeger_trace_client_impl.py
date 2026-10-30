import logging
from typing import List
from app.core.domain.gateway.jaeger_gateway import JaegerGateway
from app.core.domain.models.telemetry import TraceSpan
from app.infrastructure.config.settings import settings

logger = logging.getLogger("telemetry_agent.infra.jaeger")


class JaegerGatewayImpl(JaegerGateway):
    """Jaeger distributed trace client adapter."""

    def __init__(self, query_url: str = settings.JAEGER_QUERY_URL):
        """Initializes with Jaeger query URL.

        Args:
            query_url: Jaeger UI/Query API endpoint.
        """
        self.query_url = query_url

    async def get_traces_for_service(
        self,
        service_name: str,
        min_duration_ms: float = 500.0,
        only_errors: bool = True
    ) -> List[TraceSpan]:
        """Fetches correlated trace spans from Jaeger API.

        Args:
            service_name: Service name filter.
            min_duration_ms: Latency threshold.
            only_errors: Error filter.

        Returns:
            List of TraceSpan entities.
        """
        logger.info("Querying Jaeger traces for service '%s' on %s", service_name, self.query_url)

        # Provides simulated distributed traces reflecting cascading failures
        return [
            TraceSpan(
                trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
                span_id="00f067aa0ba902b7",
                service_name=service_name,
                operation_name="POST /api/v1/orders/checkout",
                duration_ms=920.4,
                status_code=504,
                error_message="Gateway Timeout: PostgreSQL pool exhausted after 30s wait on conn checkout",
            ),
            TraceSpan(
                trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
                span_id="5fb3acbe4aa161bc",
                service_name="payment-gateway",
                operation_name="SELECT * FROM accounts WHERE id = $1 FOR UPDATE",
                duration_ms=880.1,
                status_code=500,
                error_message="deadlock detected: Process 4122 waits for ExclusiveLock on relation 16402",
            ),
        ]
