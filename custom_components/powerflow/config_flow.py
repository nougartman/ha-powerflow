"""Config flow for Powerflow integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_AMBER_API_KEY,
    CONF_SITE_ID,
    CONF_SOLAR_SENSOR,
    CONF_LOAD_SENSOR,
    CONF_GRID_SENSOR,
    CONF_BATTERY_TYPE,
    CONF_BATTERY_SOC_SENSOR,
    CONF_PW_CAPACITY_KWH,
    CONF_TARGET_FULL_HOUR,
    CONF_PV_FORECAST_SENSOR,
    CONF_VEHICLES,
    CONF_CHARGING_RULES,
    CONF_INSTALL_COST,
    CONF_INSTALL_DATE,
    CONF_CARRY_IN_SAVINGS,
    CONF_NOVATED_LEASE,
    CONF_FUEL_PRICE_SOURCE,
    CONF_FUEL_PRICE_MANUAL,
    BATTERY_TYPE_TESSIE,
    BATTERY_TYPE_OFFICIAL,
    BATTERY_TYPE_GENERIC,
    BATTERY_TYPE_NONE,
    VEHICLE_INTEGRATION_TESSIE,
    VEHICLE_INTEGRATION_OFFICIAL,
    FUEL_SOURCE_MANUAL,
    FUEL_SOURCE_HA_SENSOR,
    FUEL_SOURCE_NSW_FUELCHECK,
    FUEL_SOURCE_QUARTERLY_AVG,
    DEFAULT_PW_CAPACITY_KWH,
    DEFAULT_TARGET_FULL_HOUR,
)
from .providers.amber import AmberProvider

_LOGGER = logging.getLogger(__name__)

PV_FORECAST_CANDIDATES = [
    "sensor.solcast_pv_forecast_forecast_remaining_today",
    "sensor.solcast_forecast_remaining_today",
    "sensor.energy_production_today_remaining",
    "sensor.open_meteo_solar_forecast_energy_production_remaining",
]


def _detect_pv_forecast_sensor(hass: HomeAssistant) -> str | None:
    """Auto-detect a PV forecast sensor from known integrations."""
    for candidate in PV_FORECAST_CANDIDATES:
        state = hass.states.get(candidate)
        if state is not None and state.state not in ("unknown", "unavailable"):
            _LOGGER.info("Auto-detected PV forecast sensor: %s", candidate)
            return candidate
    return None


class PowerflowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Powerflow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self._data: dict[str, Any] = {}
        self._vehicles: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 1 — Amber Electric API credentials."""
        errors: dict[str, str] = {}
        if user_input is not None:
            provider = AmberProvider(self.hass, user_input)
            if await provider.async_validate_credentials():
                self._data.update(user_input)
                return await self.async_step_solar()
            errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_AMBER_API_KEY): str,
                vol.Required(CONF_SITE_ID): str,
            }),
            errors=errors,
        )

    async def async_step_solar(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2 — Solar & battery sensors."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_vehicles()

        pv_default = _detect_pv_forecast_sensor(self.hass) or ""

        return self.async_show_form(
            step_id="solar",
            data_schema=vol.Schema({
                vol.Required(CONF_SOLAR_SENSOR): str,
                vol.Required(CONF_LOAD_SENSOR): str,
                vol.Required(CONF_GRID_SENSOR): str,
                vol.Required(CONF_BATTERY_TYPE, default=BATTERY_TYPE_NONE): vol.In(
                    [BATTERY_TYPE_TESSIE, BATTERY_TYPE_OFFICIAL, BATTERY_TYPE_GENERIC, BATTERY_TYPE_NONE]
                ),
                vol.Optional(CONF_BATTERY_SOC_SENSOR): str,
                vol.Optional(CONF_PW_CAPACITY_KWH, default=DEFAULT_PW_CAPACITY_KWH): vol.Coerce(float),
                vol.Optional(CONF_TARGET_FULL_HOUR, default=DEFAULT_TARGET_FULL_HOUR): vol.Coerce(float),
                vol.Optional(CONF_PV_FORECAST_SENSOR, default=pv_default): str,
            }),
        )

    async def async_step_vehicles(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 3 — Vehicle profiles."""
        if user_input is not None:
            vehicle_data = {k: v for k, v in user_input.items() if k != "add_another"}
            self._vehicles.append(vehicle_data)
            if user_input.get("add_another") and len(self._vehicles) < 4:
                return await self.async_step_vehicles()
            self._data[CONF_VEHICLES] = self._vehicles
            return await self.async_step_rules()

        return self.async_show_form(
            step_id="vehicles",
            data_schema=vol.Schema({
                vol.Required("name"): str,
                vol.Required("integration", default=VEHICLE_INTEGRATION_TESSIE): vol.In(
                    [VEHICLE_INTEGRATION_TESSIE, VEHICLE_INTEGRATION_OFFICIAL]
                ),
                vol.Required("vehicle_id"): str,
                vol.Required("charge_entity_id"): str,
                vol.Required("amps_entity_id"): str,
                vol.Optional("vin"): str,
                vol.Optional("ice_litres_per_100km", default=8.3): vol.Coerce(float),
                vol.Optional("add_another", default=False): bool,
            }),
        )

    async def async_step_rules(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 4 — Charging rules."""
        if user_input is not None:
            self._data[CONF_CHARGING_RULES] = user_input
            return await self.async_step_roi()

        return self.async_show_form(
            step_id="rules",
            data_schema=vol.Schema({
                vol.Required("peak_morning_start", default="06:00"): str,
                vol.Required("peak_morning_end", default="09:00"): str,
                vol.Required("peak_evening_start", default="17:00"): str,
                vol.Required("peak_evening_end", default="21:00"): str,
                vol.Required("overnight_start", default="00:00"): str,
                vol.Required("overnight_end", default="06:00"): str,
                vol.Required("solar_soak_start", default="11:00"): str,
                vol.Required("solar_soak_end", default="15:00"): str,
                vol.Required("overnight_soc_limit", default=40): int,
                vol.Required("max_grid_import_kw", default=18.0): vol.Coerce(float),
            }),
        )

    async def async_step_roi(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 5 — ROI & fuel price."""
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title="Powerflow", data=self._data)

        return self.async_show_form(
            step_id="roi",
            data_schema=vol.Schema({
                vol.Optional(CONF_INSTALL_COST, default=0.0): vol.Coerce(float),
                vol.Optional(CONF_INSTALL_DATE): str,
                vol.Optional(CONF_CARRY_IN_SAVINGS, default=0.0): vol.Coerce(float),
                vol.Optional(CONF_NOVATED_LEASE, default=False): bool,
                vol.Required(CONF_FUEL_PRICE_SOURCE, default=FUEL_SOURCE_QUARTERLY_AVG): vol.In(
                    [FUEL_SOURCE_MANUAL, FUEL_SOURCE_HA_SENSOR, FUEL_SOURCE_NSW_FUELCHECK, FUEL_SOURCE_QUARTERLY_AVG]
                ),
                vol.Optional(CONF_FUEL_PRICE_MANUAL): vol.Coerce(float),
            }),
        )
