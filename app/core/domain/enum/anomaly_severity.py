from enum import Enum


class AnomalySeverity(str, Enum):
    """Categorization of incident criticality detected by autonomous agents."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class MetricType(str, Enum):
    """Class of telemetry metric under observation."""

    LATENCY_P99 = "LATENCY_P99"
    ERROR_RATE_5XX = "ERROR_RATE_5XX"
    CPU_USAGE = "CPU_USAGE"
    MEMORY_PRESSURE = "MEMORY_PRESSURE"
