"""Official Tesla HA integration vehicle controller."""
from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant

from .base import VehicleController

_LOGGER = logging.getLogger(__name__)


class OfficialTeslaController(VehicleController):
    """Controls a Tesla vehicle via the official Tesla HA integration."""

    def __init__(self, hass: HomeAssistant, charge_entity_id: str) -> None:
        """Initialise controller."""
        self.hass = hass
        self.charge_entity_id = charge_entity_id

    async def async_wake(self) -> None:
        """Wake via official Tesla integration."""
        _LOGGER.debug("Official Tesla: waking via %s", self.charge_entity_id)
        await self.hass.services.async_call(
            "tesla_custom", "api",
            {"entity_id": self.charge_entity_id, "command": "WAKE_UP"},
            blocking=True,
        )

    async def async_start_charge(self) -> None:
        """Start charging via official integration."""
        await self.hass.services.async_call(
            "switch", "turn_on", {"entity_id": self.charge_entity_id}, blocking=True
        )

    async def async_stop_charge(self) -> None:
        """Stop charging via official integration."""
        await self.hass.services.async_call(
            "switch", "turn_off", {"entity_id": self.charge_entity_id}, blocking=True
        )

    async def async_set_charge_current(self, amps: int) -> None:
        """Set charging current via official integration."""
        _LOGGER.debug("Official Tesla: set charge amps -> %dA", amps)
        await self.hass.services.async_call(
            "number", "set_value",
            {"entity_id": self.charge_entity_id.replace("switch.", "number.").replace("_charger", "_charge_amps"), "value": amps},
            blocking=True,
        )
