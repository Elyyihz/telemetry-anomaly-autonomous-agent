from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for Telemetry Anomaly Autonomous Agent."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "telemetry-anomaly-autonomous-agent"
    APP_VERSION: str = "1.0.0"
    LOG_LEVEL: str = "INFO"

    # Prometheus
    PROMETHEUS_URL: str = "http://prometheus:9090"

    # Jaeger
    JAEGER_QUERY_URL: str = "http://jaeger:16686"

    # llama.cpp Local Model
    LLAMA_CPP_MODEL_PATH: str = "/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    LLAMA_CPP_API_BASE: str = "http://localhost:8080/v1"
    LLAMA_CPP_CTX_SIZE: int = 4096


settings = Settings()
