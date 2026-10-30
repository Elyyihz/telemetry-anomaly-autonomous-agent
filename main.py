import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.presentation.api.v1.router import router as api_router
from app.infrastructure.config.settings import settings

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("telemetry_agent.main")

app = FastAPI(
    title="Detector de Anomalias de Telemetria com Agentes Autônomos",
    description="Agente autônomo baseado em LangGraph e llama.cpp que consome métricas do Prometheus e traces do Jaeger para diagnóstico de causa raiz.",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "cli_usage": "python -m app.presentation.cli.diagnose_cli <service_name>",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
