"""Tests for the AmberProvider 48-interval forecast parsing."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from custom_components.powerflow.providers.amber import AmberProvider


def _build_provider(config_entry_data):
    hass = MagicMock()
    hass.states.get.return_value = None
    return AmberProvider(hass, config_entry_data)


def test_parse_intervals_extracts_current_price(config_entry_data, mock_amber_intervals):
    """Parser should extract current_price from CurrentInterval."""
    provider = _build_provider(config_entry_data)
    result = provider._parse_intervals(mock_amber_intervals)
    assert "current_price" in result
    assert isinstance(result["current_price"], float)


def test_parse_intervals_sets_forecast_min_max(config_entry_data, mock_amber_intervals):
    """Forecast min/max should be computed across all ForecastIntervals."""
    provider = _build_provider(config_entry_data)
    result = provider._parse_intervals(mock_amber_intervals)
    assert result["forecast_12h_min"] <= result["forecast_12h_max"]
    assert result["forecast_12h_min"] <= result["forecast_12h_avg"]


def test_parse_intervals_spike_detection(config_entry_data):
    """spikeStatus='spike' in any ForecastInterval must set spike_warning_12h."""
    provider = _build_provider(config_entry_data)
    intervals = [
        {"type": "CurrentInterval", "channelType": "general", "perKwh": 10, "descriptor": "neutral", "spikeStatus": "none"},
        {"type": "ForecastInterval", "channelType": "general", "perKwh": 50, "descriptor": "spike", "spikeStatus": "spike"},
    ]
    result = provider._parse_intervals(intervals)
    assert result["spike_warning_12h"] is True


def test_parse_intervals_no_spike(config_entry_data):
    """No ForecastInterval with spike -> spike_warning_12h should be False."""
    provider = _build_provider(config_entry_data)
    intervals = [
        {"type": "CurrentInterval", "channelType": "general", "perKwh": 8, "descriptor": "low", "spikeStatus": "none"},
        {"type": "ForecastInterval", "channelType": "general", "perKwh": 5, "descriptor": "low", "spikeStatus": "none"},
    ]
    result = provider._parse_intervals(intervals)
    assert result["spike_warning_12h"] is False
