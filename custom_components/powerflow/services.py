"""Services for Powerflow integration."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN
from .engines.reimbursement import ReimbursementEngine
from .vehicles.tessie import TessieController
from .vehicles.official_tesla import OfficialTeslaController

_LOGGER = logging.getLogger(__name__)


def _get_coordinator(hass: HomeAssistant):
    """Retrieve the first available coordinator."""
    entries = hass.data.get(DOMAIN, {})
    if not entries:
        _LOGGER.error("Powerflow is not configured")
        return None
    return next(iter(entries.values()))


def _get_vehicle_controller(hass: HomeAssistant, vehicle_id: str):
    """Build a vehicle controller from config."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        return None
    vehicles = coordinator.entry.data.get("vehicles", [])
    vehicle = next((v for v in vehicles if v["vehicle_id"] == vehicle_id), None)
    if not vehicle:
        _LOGGER.warning("Vehicle '%s' not found in config", vehicle_id)
        return None
    if vehicle.get("integration") == "tessie":
        return TessieController(hass, vehicle["vehicle_id"])
    if vehicle.get("integration") == "official_tesla":
        return OfficialTeslaController(hass, vehicle["charge_entity_id"])
    _LOGGER.warning("Unknown integration type for vehicle '%s'", vehicle_id)
    return None


async def async_register_services(hass: HomeAssistant) -> None:
    """Register all Powerflow services."""
    if hass.services.has_service(DOMAIN, "start_charge"):
        return  # Already registered (multiple config entries)

    async def handle_start_charge(call: ServiceCall) -> None:
        vid = call.data["vehicle_id"]
        if ctrl := _get_vehicle_controller(hass, vid):
            _LOGGER.info("Starting charge for vehicle '%s'", vid)
            await ctrl.async_wake()
            await ctrl.async_start_charge()

    async def handle_stop_charge(call: ServiceCall) -> None:
        vid = call.data["vehicle_id"]
        if ctrl := _get_vehicle_controller(hass, vid):
            _LOGGER.info("Stopping charge for vehicle '%s'", vid)
            await ctrl.async_stop_charge()

    async def handle_set_charge_current(call: ServiceCall) -> None:
        vid = call.data["vehicle_id"]
        amps = int(call.data["amps"])
        if ctrl := _get_vehicle_controller(hass, vid):
            _LOGGER.info("Setting charge current for '%s' to %dA", vid, amps)
            await ctrl.async_set_charge_current(amps)

    async def handle_log_away_charge(call: ServiceCall) -> None:
        """Log a charging session that occurred away from home."""
        coordinator = _get_coordinator(hass)
        if not coordinator:
            return
        from .storage.session_store import SessionStore
        store = SessionStore(hass)
        session: dict[str, Any] = {
            "vehicle_id": call.data.get("vehicle_id"),
            "energy_added_kwh": float(call.data.get("energy_added_kwh", 0)),
            "starting_soc": int(call.data.get("starting_soc", 0)),
            "ending_soc": int(call.data.get("ending_soc", 0)),
            "grid_fraction": float(call.data.get("grid_fraction", 1.0)),
            "grid_cost": float(call.data.get("grid_cost", 0)),
            "ended_at": call.data.get("ended_at"),
            "away": True,
        }
        await store.async_append_session(session)
        _LOGGER.info("Logged away session for vehicle '%s'", session["vehicle_id"])

    async def handle_export_reimbursement_csv(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass)
        if not coordinator:
            return
        engine = ReimbursementEngine(hass, coordinator.entry.data)
        vid = call.data["vehicle_id"]
        now = datetime.now()
        start, end = engine.get_billing_cycle_boundaries(now)
        csv_data = await engine.async_export_csv(vid, start, end)
        _LOGGER.info("CSV export ready for vehicle '%s' (%d bytes)", vid, len(csv_data))

    async def handle_recalculate_fuel_savings(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass)
        if not coordinator:
            return
        _LOGGER.info("Recalculating fuel savings")
        await coordinator.async_refresh()

    hass.services.async_register(DOMAIN, "start_charge", handle_start_charge,
        schema=vol.Schema({vol.Required("vehicle_id"): str}))
    hass.services.async_register(DOMAIN, "stop_charge", handle_stop_charge,
        schema=vol.Schema({vol.Required("vehicle_id"): str}))
    hass.services.async_register(DOMAIN, "set_charge_current", handle_set_charge_current,
        schema=vol.Schema({vol.Required("vehicle_id"): str, vol.Required("amps"): int}))
    hass.services.async_register(DOMAIN, "log_away_charge", handle_log_away_charge)
    hass.services.async_register(DOMAIN, "export_reimbursement_csv", handle_export_reimbursement_csv)
    hass.services.async_register(DOMAIN, "recalculate_fuel_savings", handle_recalculate_fuel_savings)
