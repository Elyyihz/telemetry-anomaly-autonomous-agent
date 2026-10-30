from app.core.usecase.anomaly_agent.state import TelemetryAgentState
from app.core.domain.enum.anomaly_severity import AnomalySeverity


def routing_anomaly_detected(state: TelemetryAgentState) -> str:
    """Routes execution based on whether metric anomalies were found.

    Args:
        state: Active agent state.

    Returns:
        Edge branch identifier: 'investigate_traces' or 'healthy_conclude'.
    """
    anomalies = state.get("anomalies", [])
    if anomalies and len(anomalies) > 0:
        return "investigate_traces"
    return "healthy_conclude"
