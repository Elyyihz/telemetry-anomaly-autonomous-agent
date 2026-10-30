from langgraph.graph import StateGraph, END
from app.core.usecase.anomaly_agent.state import TelemetryAgentState
from app.core.usecase.anomaly_agent.nodes import TelemetryAgentNodes
from app.core.usecase.anomaly_agent.edges import routing_anomaly_detected


class TelemetryAgentGraphUseCase:
    """Compiles the LangGraph state machine for autonomous telemetry diagnostics."""

    def __init__(self, nodes: TelemetryAgentNodes):
        """Initializes orchestrator with node provider.

        Args:
            nodes: TelemetryAgentNodes instance with injected gateway dependencies.
        """
        self.nodes = nodes
        self.workflow = self._compile_graph()

    def _compile_graph(self):
        """Builds and compiles the StateGraph workflow."""
        builder = StateGraph(TelemetryAgentState)

        # 1. Register Nodes
        builder.add_node("node_fetch_metrics", self.nodes.node_fetch_metrics)
        builder.add_node("node_evaluate_anomalies", self.nodes.node_evaluate_anomalies)
        builder.add_node("node_fetch_correlated_traces", self.nodes.node_fetch_correlated_traces)
        builder.add_node("node_diagnose_root_cause_llm", self.nodes.node_diagnose_root_cause_llm)

        # 2. Entry point
        builder.set_entry_point("node_fetch_metrics")

        # 3. Transitions
        builder.add_edge("node_fetch_metrics", "node_evaluate_anomalies")

        builder.add_conditional_edges(
            "node_evaluate_anomalies",
            routing_anomaly_detected,
            {
                "investigate_traces": "node_fetch_correlated_traces",
                "healthy_conclude": END,
            },
        )

        builder.add_edge("node_fetch_correlated_traces", "node_diagnose_root_cause_llm")
        builder.add_edge("node_diagnose_root_cause_llm", END)

        return builder.compile()

    async def execute(self, initial_state: TelemetryAgentState) -> TelemetryAgentState:
        """Executes the compiled LangGraph workflow.

        Args:
            initial_state: Initial state payload.

        Returns:
            Terminal state containing metrics, traces, and LLM diagnosis.
        """
        return await self.workflow.ainvoke(initial_state)
