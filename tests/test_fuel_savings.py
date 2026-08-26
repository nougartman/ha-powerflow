"""Tests for FuelSavingsEngine."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.powerflow.engines.fuel_savings import FuelSavingsEngine


@pytest.mark.asyncio
async def test_manual_fuel_price(config_entry_data):
    """When manual source is selected the config value is returned."""
    data = {**config_entry_data, "fuel_price_source": "manual", "fuel_price_manual": 2.25}
    engine = FuelSavingsEngine(MagicMock(), data)
    assert await engine.async_get_fuel_price() == pytest.approx(2.25)


@pytest.mark.asyncio
async def test_quarterly_avg_fallback(config_entry_data):
    """Quarterly avg source should return a reasonable AUS price (>1.0)."""
    data = {**config_entry_data, "fuel_price_source": "quarterly_avg"}
    engine = FuelSavingsEngine(MagicMock(), data)
    price = await engine.async_get_fuel_price()
    assert price > 1.0


@pytest.mark.asyncio
async def test_get_stats_zero_when_no_data(config_entry_data):
    """With empty store, fleet savings should be zero."""
    with patch(
        "custom_components.powerflow.engines.fuel_savings.PowerflowStore"
    ) as mock_store_class:
        mock_store = MagicMock()
        mock_store.async_load = AsyncMock(return_value={})
        mock_store_class.return_value = mock_store
        engine = FuelSavingsEngine(MagicMock(), config_entry_data)
        stats = await engine.async_get_stats()

    assert stats["fleet_fuel_savings"] == 0.0
    assert stats["fleet_petrol_avoided"] == 0.0
