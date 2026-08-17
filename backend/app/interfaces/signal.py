from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class SignalProvider(ABC):
    """
    Abstract Interface for Signal Engine.
    Will generate BUY CE, BUY PE, WATCH, NO TRADE signals in future phases.
    """

    @abstractmethod
    async def evaluate_signal(self, symbol: str) -> Dict[str, Any]:
        pass
