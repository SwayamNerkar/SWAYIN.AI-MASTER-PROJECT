import pytest
from app.services.caching_service import cache_service
from app.services.market_data_service import market_data_service
from app.schemas.market_data import MarketSnapshot

@pytest.mark.asyncio
async def test_in_memory_cache():
    await cache_service.set("test_key", "hello_swayin", ttl_seconds=2.0)
    val = await cache_service.get("test_key")
    assert val == "hello_swayin"
    await cache_service.delete("test_key")
    assert await cache_service.get("test_key") is None

@pytest.mark.asyncio
async def test_market_snapshot_service():
    snapshot = await market_data_service.get_market_snapshot()
    assert isinstance(snapshot, MarketSnapshot)
    assert snapshot.nifty.symbol == "NIFTY"
    assert snapshot.sensex.symbol == "SENSEX"
    assert snapshot.data_health.validation_passed is True
    assert snapshot.data_health.nifty_age_seconds >= 0.0
    assert snapshot.data_health.sensex_age_seconds >= 0.0
