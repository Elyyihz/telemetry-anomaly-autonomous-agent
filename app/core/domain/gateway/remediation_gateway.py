from abc import ABC, abstractmethod
from typing import Dict, Any


class RemediationGateway(ABC):
    """Abstract interface defining autonomous self-healing and remediation execution."""

    @abstractmethod
    async def execute_remediation(
        self, action: str, service_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatches automated self-healing action to infrastructure control plane or webhook.

        Args:
            action: Remediation verb (e.g. 'RESTART_POD', 'CLEAR_CACHE', 'SCALE_UP').
            service_name: Name of target service.
            parameters: Action-specific arguments.

        Returns:
            Dictionary containing remediation outcome and metadata.
        """
        pass
