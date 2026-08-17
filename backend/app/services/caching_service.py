import time
import asyncio
from typing import Dict, Any, Optional
from app.core.config import settings

class MarketDataCacheService:
    """
    In-Memory Caching Subsystem for Market Data.
    Provides fast, thread-safe access to quotes, snapshots, and option chains.
    Designed with a clean interface for seamless Redis integration in future phases.
    """

    def __init__(self, enabled: bool = settings.MARKET_DATA_CACHE_ENABLED):
        self.enabled = enabled
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Retrieves cached item if present and not expired."""
        if not self.enabled:
            return None

        async with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None

            expires_at = entry.get("expires_at")
            if expires_at and time.time() > expires_at:
                del self._store[key]
                return None

            return entry.get("value")

    async def set(self, key: str, value: Any, ttl_seconds: float = 5.0) -> None:
        """Stores item in cache with Time-To-Live (TTL) in seconds."""
        if not self.enabled:
            return

        expires_at = time.time() + ttl_seconds if ttl_seconds > 0 else None
        async with self._lock:
            self._store[key] = {
                "value": value,
                "created_at": time.time(),
                "expires_at": expires_at
            }

    async def delete(self, key: str) -> None:
        """Removes a key from cache."""
        async with self._lock:
            self._store.pop(key, None)

    async def clear(self) -> None:
        """Clears all cached entries."""
        async with self._lock:
            self._store.clear()

    async def get_stats(self) -> Dict[str, Any]:
        """Returns cache statistics."""
        async with self._lock:
            total_items = len(self._store)
            active_items = sum(1 for entry in self._store.values() if not entry.get("expires_at") or time.time() <= entry.get("expires_at"))
            return {
                "enabled": self.enabled,
                "total_entries": total_items,
                "active_entries": active_items
            }

cache_service = MarketDataCacheService()
