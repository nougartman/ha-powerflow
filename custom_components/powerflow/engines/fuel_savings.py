"""Fuel savings engine for Powerflow."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant

from ..const import (
    FUEL_SOURCE_MANUAL,
    FUEL_SOURCE_HA_SENSOR,
    FUEL_SOURCE_NSW_FUELCHECK,
    FUEL_SOURCE_QUARTERLY_AVG,
    HISTORICAL_ULP91_PRICE,
    CONF_FUEL_PRICE_SOURCE,
    CONF_FUEL_PRICE_MANUAL,
    NSW_FUELCHECK_API_BASE,
)
from ..storage.ha_store import PowerflowStore

_LOGGER = logging.getLogger(__name__)


class FuelSavingsEngine:
    """Tracks EV fuel savings vs ICE equivalent per vehicle and fleet."""

    def __init__(self, hass: HomeAssistant, config_data: dict[str, Any]) -> None:
        """Initialise engine."""
        self.hass = hass
        self.config = config_data
        self.store = PowerflowStore(hass)

    def _current_quarter_key(self) -> str:
        """Return current year-Q key e.g. '2026-Q3'."""
        now = datetime.now()
        q = (now.month - 1) // 3 + 1
        return f"{now.year}-Q{q}"

    async def async_get_fuel_price(self) -> float:
        """Determine fuel price using tiered 5-source strategy."""
        source = self.config.get(CONF_FUEL_PRICE_SOURCE, FUEL_SOURCE_QUARTERLY_AVG)

        if source == FUEL_SOURCE_MANUAL:
            return float(self.config.get(CONF_FUEL_PRICE_MANUAL, 2.10))

        if source == FUEL_SOURCE_HA_SENSOR:
            sensor_id = self.config.get("fuel_price_sensor")
            if sensor_id:
                state = self.hass.states.get(sensor_id)
                if state and state.state not in ("unknown", "unavailable"):
                    try:
                        return float(state.state)
                    except ValueError:
                        pass

        if source == FUEL_SOURCE_NSW_FUELCHECK:
            try:
                api_key = self.config.get("nsw_fuelcheck_key")
                if not api_key:
                    raise ValueError("No NSW FuelCheck API key configured")
                price = await self._fetch_nsw_fuel_price(api_key)
                if price is not None:
                    return price
            except Exception as err:
                _LOGGER.warning("Failed to fetch NSW FuelCheck price: %s", err)

        # Quarterly average fallback
        key = self._current_quarter_key()
        price = HISTORICAL_ULP91_PRICE.get(key)
        if price is not None:
            return price
        # Ultimate fallback: most recent known value
        return list(HISTORICAL_ULP91_PRICE.values())[-1] if HISTORICAL_ULP91_PRICE else 2.10

    async def _fetch_nsw_fuel_price(self, api_key: str) -> float | None:
        """Fetch ULP91 price from NSW FuelCheck API."""
        zone = self.hass.states.get("zone.home")
        if not zone:
            return None
        lat = zone.attributes.get("latitude")
        lon = zone.attributes.get("longitude")
        if not lat or not lon:
            return None

        params = {"fuelType": "U", "latitude": str(lat), "longitude": str(lon), "radius": "5", "noOfResults": "10"}
        headers = {"ApiKey": api_key, "Content-Type": "application/json"}
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(NSW_FUELCHECK_API_BASE, params=params, headers=headers) as resp:
                resp.raise_for_status()
                data = await resp.json()

        stations = data.get("stations", []) or data.get("fstations", [])
        prices = []
        for station in stations:
            for price in station.get("prices", []):
                if price.get("type") == "U":
                    try:
                        prices.append(float(price.get("price", 0)) / 100.0)
                    except (TypeError, ValueError):
                        pass
        return sum(prices) / len(prices) if prices else None

    async def async_get_stats(self) -> dict:
        """Get aggregated fleet fuel savings stats."""
        data = await self.store.async_load()
        local_e91 = await self.async_get_fuel_price()

        fleet_fuel_savings = 0.0
        fleet_petrol_avoided = 0.0
        fleet_distance_tracked = 0.0
        fleet_ice_fuel_cost = 0.0
        fleet_ev_charging_cost = 0.0
        per_vehicle = {}

        for vehicle in self.config.get("vehicles", []):
            vid = vehicle["vehicle_id"]
            ice_l = float(vehicle.get("ice_litres_per_100km", 8.3))
            v_data = data.get(vid, {})
            distance = float(v_data.get("distance_tracked", 0.0))
            ev_cost = float(v_data.get("ev_charging_cost", 0.0))
            ice_cost = distance * (ice_l / 100.0) * local_e91
            savings = ice_cost - ev_cost
            petrol_avoided = distance * (ice_l / 100.0)

            fleet_fuel_savings += savings
            fleet_petrol_avoided += petrol_avoided
            fleet_distance_tracked += distance
            fleet_ice_fuel_cost += ice_cost
            fleet_ev_charging_cost += ev_cost

            per_vehicle[vid] = {
                "fuel_savings": round(savings, 2),
                "petrol_avoided": round(petrol_avoided, 2),
                "distance_tracked": round(distance, 1),
                "ice_fuel_cost": round(ice_cost, 2),
                "ev_charging_cost": round(ev_cost, 2),
            }

        return {
            "fleet_fuel_savings": round(fleet_fuel_savings, 2),
            "fleet_petrol_avoided": round(fleet_petrol_avoided, 2),
            "fleet_distance_tracked": round(fleet_distance_tracked, 1),
            "fleet_ice_fuel_cost": round(fleet_ice_fuel_cost, 2),
            "fleet_ev_charging_cost": round(fleet_ev_charging_cost, 2),
            "per_vehicle": per_vehicle,
            "local_e91_fuel_price": local_e91,
        }
