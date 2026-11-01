import uuid
from typing import Optional, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.core.usecase.anomaly_agent.state import TelemetryAgentState
from app.core.usecase.anomaly_agent.nodes import TelemetryAgentNodes
from app.core.usecase.anomaly_agent.edges import routing_anomaly_detected


class TelemetryAgentGraphUseCase:
    """Compiles the LangGraph state machine with persistence and self-healing nodes."""

    def __init__(self, nodes: TelemetryAgentNodes, checkpointer: Optional[Any] = None):
        """Initializes orchestrator with node provider and persistent checkpointer.

        Args:
            nodes: TelemetryAgentNodes instance with injected gateway dependencies.
            checkpointer: Optional LangGraph checkpointer (defaults to in-memory MemorySaver).
        """
        self.nodes = nodes
        self.checkpointer = checkpointer or MemorySaver()
        self.workflow = self._compile_graph()

    def _compile_graph(self):
        """Builds and compiles the StateGraph workflow with state checkpointing."""
        builder = StateGraph(TelemetryAgentState)

        # 1. Register Nodes
        builder.add_node("node_fetch_metrics", self.nodes.node_fetch_metrics)
        builder.add_node("node_evaluate_anomalies", self.nodes.node_evaluate_anomalies)
        builder.add_node("node_fetch_correlated_traces", self.nodes.node_fetch_correlated_traces)
        builder.add_node("node_diagnose_root_cause_llm", self.nodes.node_diagnose_root_cause_llm)
        builder.add_node("node_auto_remediate", self.nodes.node_auto_remediate)

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
        builder.add_edge("node_diagnose_root_cause_llm", "node_auto_remediate")
        builder.add_edge("node_auto_remediate", END)

        return builder.compile(checkpointer=self.checkpointer)

    async def execute(
        self, initial_state: TelemetryAgentState, thread_id: Optional[str] = None
    ) -> TelemetryAgentState:
        """Executes the compiled LangGraph workflow with thread tracking.

        Args:
            initial_state: Initial state payload.
            thread_id: Optional correlation thread ID for checkpoint history.

        Returns:
            Terminal state containing metrics, traces, LLM diagnosis, and remediation.
        """
        config = {"configurable": {"thread_id": thread_id or str(uuid.uuid4())}}
        return await self.workflow.ainvoke(initial_state, config=config)
