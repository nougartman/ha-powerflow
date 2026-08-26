"""Test fixtures for Powerflow."""
from __future__ import annotations

import pytest


@pytest.fixture
def config_entry_data() -> dict:
    """Realistic config entry for a one-vehicle setup."""
    return {
        "amber_api_key": "test_amber_key_123",
        "site_id": "test_site_abc",
        "solar_sensor": "sensor.solar_power",
        "load_sensor": "sensor.home_load",
        "grid_sensor": "sensor.grid_power",
        "battery_type": "tessie_powerwall",
        "battery_soc_sensor": "sensor.pw_soc",
        "pw_capacity_kwh": 13.5,
        "target_full_hour": 15.0,
        "pv_forecast_sensor": "sensor.solcast_forecast_remaining_today",
        "vehicles": [
            {
                "name": "Hot Dog",
                "vehicle_id": "hot_dog",
                "integration": "tessie",
                "charge_entity_id": "switch.hot_dog_charge",
                "amps_entity_id": "number.hot_dog_charge_current",
                "ice_litres_per_100km": 8.3,
            }
        ],
        "charging_rules": {
            "peak_morning_start": "06:00",
            "peak_morning_end": "09:00",
            "peak_evening_start": "17:00",
            "peak_evening_end": "21:00",
            "overnight_start": "00:00",
            "overnight_end": "06:00",
            "solar_soak_start": "11:00",
            "solar_soak_end": "15:00",
            "overnight_soc_limit": 40,
            "max_grid_import_kw": 18.0,
        },
        "fuel_price_source": "quarterly_avg",
    }


@pytest.fixture
def mock_amber_intervals() -> list:
    """Realistic 48-interval Amber API response fixture."""
    descriptors = [
        "neutral", "low", "extremelyLow", "negative", "extremelyLow",
        "low", "neutral", "neutral", "high", "spike",
    ]
    intervals = []
    for i in range(48):
        is_current = i == 0
        intervals.append({
            "type": "CurrentInterval" if is_current else "ForecastInterval",
            "channelType": "general",
            "perKwh": 10 - (i % 15),
            "descriptor": descriptors[i % len(descriptors)],
            "spikeStatus": "spike" if descriptors[i % len(descriptors)] == "spike" else "none",
        })
    return intervals
