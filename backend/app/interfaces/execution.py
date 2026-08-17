from abc import ABC, abstractmethod
from typing import Dict, Any

class ExecutionProvider(ABC):
    """
    Abstract Interface for Execution Engine (Paper / Manual / Automated).
    Decouples signal generation from execution mechanics.
    """

    @abstractmethod
    async def execute_trade_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        pass
