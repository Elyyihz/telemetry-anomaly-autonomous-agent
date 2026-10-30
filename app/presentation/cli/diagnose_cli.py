import asyncio
import sys
from app.infrastructure.gateway.prometheus_client_impl import PrometheusGatewayImpl
from app.infrastructure.gateway.jaeger_trace_client_impl import JaegerGatewayImpl
from app.infrastructure.gateway.llama_cpp_client_impl import LlamaCppGatewayImpl
from app.infrastructure.gateway.incident_notifier_impl import IncidentNotifierGatewayImpl
from app.core.usecase.anomaly_agent.nodes import TelemetryAgentNodes
from app.core.usecase.anomaly_agent.graph import TelemetryAgentGraphUseCase
from app.core.usecase.diagnose_infrastructure_usecase import DiagnoseInfrastructureUseCase


async def run_cli():
    """Runs on-demand terminal diagnosis."""
    svc = sys.argv[1] if len(sys.argv) > 1 else "checkout-service"
    print(f"\n🔍 [AGENTE DE TELEMETRIA] Iniciando diagnóstico autônomo para o serviço '{svc}'...\n")

    nodes = TelemetryAgentNodes(
        prometheus_gateway=PrometheusGatewayImpl(),
        jaeger_gateway=JaegerGatewayImpl(),
        local_llm_gateway=LlamaCppGatewayImpl(),
    )
    graph_uc = TelemetryAgentGraphUseCase(nodes)
    diag_uc = DiagnoseInfrastructureUseCase(graph_uc, IncidentNotifierGatewayImpl())

    result = await diag_uc.execute(svc)

    print("=" * 70)
    print(f"📊 SERVIÇO: {result['service_name']} | SEVERIDADE: {result['severity']}")
    print(f"🚨 ANOMALIAS DETECTADAS: {len(result.get('anomalies', []))}")
    print(f"🔗 TRACES CORRELACIONADOS: {len(result.get('traces', []))}")
    print("=" * 70)

    if result.get("diagnosis"):
        diag = result["diagnosis"]
        print(f"\n🧠 CAUSA RAIZ IDENTIFICADA (llama.cpp - Confiança: {diag['confidence_score'] * 100:.1f}%):")
        print(f"   {diag['root_cause_summary']}\n")
        print("🛠️ AÇÕES RECOMENDADAS:")
        for idx, act in enumerate(diag["recommended_actions"], 1):
            print(f"   {idx}. {act}")
        if diag.get("auto_remediation_suggested"):
            print(f"\n⚡ REMEDIAÇÃO AUTOMATIZADA SUGERIDA: {diag['auto_remediation_suggested']}")
    else:
        print("\n✅ Sistema operando em parâmetros normais.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(run_cli())
