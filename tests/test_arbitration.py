"""Tests for the ArbitrationEngine."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from custom_components.powerflow.engines.arbitration import ArbitrationEngine


def _make_hass(states):
    hass = MagicMock()
    hass.states.get.side_effect = lambda entity_id: states.get(entity_id)
    return hass


def _make_state(value: str):
    s = MagicMock()
    s.state = value
    return s


@pytest.mark.asyncio
async def test_peak_lockout(config_entry_data):
    """During morning peak charge_desired must be False."""
    states = {
        "sensor.solar_power": _make_state("3.5"),
        "sensor.home_load": _make_state("1.2"),
        "sensor.pw_soc": _make_state("75"),
    }
    engine = ArbitrationEngine(_make_hass(states), config_entry_data)
    result = await engine.async_evaluate({"descriptor": "high", "spike_status": "potential"})
    assert "hot_dog" in result
    assert result["hot_dog"]["charge_desired"] is False
    assert "Peak" in result["hot_dog"]["reason"]


@pytest.mark.asyncio
async def test_cheap_rate_charges(config_entry_data):
    """When Amber descriptor is extremelyLow, charge must be desired."""
    states = {
        "sensor.solar_power": _make_state("0"),
        "sensor.home_load": _make_state("1.5"),
        "sensor.pw_soc": _make_state("30"),
    }
    engine = ArbitrationEngine(_make_hass(states), config_entry_data)
    result = await engine.async_evaluate({"descriptor": "extremelyLow", "spike_status": "none"})
    assert result["hot_dog"]["charge_desired"] is True


@pytest.mark.asyncio
async def test_solar_soak_charges(config_entry_data):
    """When solar_soak_predicted and excess > 1.2kW, soak mode activates."""
    states = {
        "sensor.solar_power": _make_state("5.0"),
        "sensor.home_load": _make_state("1.5"),
        "sensor.pw_soc": _make_state("40"),
    }
    engine = ArbitrationEngine(_make_hass(states), config_entry_data)
    result = await engine.async_evaluate({
        "descriptor": "extremelyLow",
        "spike_status": "none",
        "solar_soak_predicted": True,
    })
    assert result["hot_dog"]["charge_desired"] is True
    assert "Solar Soak" in result["hot_dog"]["reason"]
    assert result["hot_dog"]["target_amps"] == 32


@pytest.mark.asyncio
async def test_idle_when_neutral(config_entry_data):
    """Neutral price and no special window -> idle."""
    states = {
        "sensor.solar_power": _make_state("0"),
        "sensor.home_load": _make_state("1.5"),
        "sensor.pw_soc": _make_state("70"),
    }
    engine = ArbitrationEngine(_make_hass(states), config_entry_data)
    result = await engine.async_evaluate({"descriptor": "neutral", "spike_status": "none"})
    assert result["hot_dog"]["charge_desired"] is False
