"""Tessie vehicle controller for Powerflow."""
from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant

from .base import VehicleController

_LOGGER = logging.getLogger(__name__)


class TessieController(VehicleController):
    """Controls a Tesla vehicle via the Tessie HA integration."""

    def __init__(self, hass: HomeAssistant, vehicle_id: str) -> None:
        """Initialise controller."""
        self.hass = hass
        self.vehicle_id = vehicle_id

    def _get_tessie_token(self) -> str | None:
        """Extract the Tessie access token from its config entry."""
        for entry in self.hass.config_entries.async_entries("tessie"):
            token = entry.data.get("access_token")
            if token:
                return token
        return None

    async def async_wake(self) -> None:
        """Wake the vehicle via Tessie."""
        _LOGGER.debug("Tessie: waking vehicle %s", self.vehicle_id)
        await self.hass.services.async_call(
            "tessie", "wake", {"device_id": self.vehicle_id}, blocking=True
        )

    async def async_start_charge(self) -> None:
        """Start charging via Tessie."""
        _LOGGER.debug("Tessie: start charge %s", self.vehicle_id)
        await self.hass.services.async_call(
            "tessie", "start_charging", {"device_id": self.vehicle_id}, blocking=True
        )

    async def async_stop_charge(self) -> None:
        """Stop charging via Tessie."""
        _LOGGER.debug("Tessie: stop charge %s", self.vehicle_id)
        await self.hass.services.async_call(
            "tessie", "stop_charging", {"device_id": self.vehicle_id}, blocking=True
        )

    async def async_set_charge_current(self, amps: int) -> None:
        """Set charging current via Tessie."""
        _LOGGER.debug("Tessie: set charge current %s -> %dA", self.vehicle_id, amps)
        await self.hass.services.async_call(
            "tessie",
            "set_charge_amps",
            {"device_id": self.vehicle_id, "charge_amps": amps},
            blocking=True,
        )
