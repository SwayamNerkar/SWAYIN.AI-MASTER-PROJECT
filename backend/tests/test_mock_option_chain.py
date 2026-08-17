import pytest
from app.adapters.mock.mock_option_chain import MockOptionChainAdapter

chain_adapter = MockOptionChainAdapter()

@pytest.mark.asyncio
async def test_atm_strike_calculation():
    atm = await chain_adapter.get_atm_strike("NIFTY")
    assert atm % 50 == 0

@pytest.mark.asyncio
async def test_option_chain_structure():
    data = await chain_adapter.get_option_chain("NIFTY")
    assert data["underlying"] == "NIFTY"
    assert "spot_price" in data
    assert "chain" in data
    assert len(data["chain"]) > 0

    first_strike = data["chain"][0]
    assert "strike_price" in first_strike
    assert "CE" in first_strike
    assert "PE" in first_strike
    assert first_strike["CE"]["ltp"] > 0
    assert first_strike["PE"]["ltp"] > 0
    assert first_strike["CE"]["oi"] > 0
