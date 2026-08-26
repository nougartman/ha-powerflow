"""DataUpdateCoordinator for Powerflow."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .providers.amber import AmberProvider
from .engines.arbitration import ArbitrationEngine
from .engines.fuel_savings import FuelSavingsEngine
from .engines.roi import ROIEngine

_LOGGER = logging.getLogger(__name__)


class PowerflowCoordinator(DataUpdateCoordinator):
    """Manages fetching Powerflow data from multiple sources every 5 minutes."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Powerflow Coordinator",
            update_interval=timedelta(seconds=300),
        )
        self.entry_id = entry.entry_id
        self.entry = entry

        self.amber_provider = AmberProvider(hass, entry.data)
        self.arbitration_engine = ArbitrationEngine(hass, entry.data)
        self.fuel_savings_engine = FuelSavingsEngine(hass, entry.data)
        self.roi_engine = ROIEngine(hass, entry.data)

    async def _async_update_data(self) -> dict:
        """Fetch and aggregate data from all sources."""
        try:
            amber_data = await self.amber_provider.async_fetch_prices()
            arbitration_data = await self.arbitration_engine.async_evaluate(amber_data)
            fuel_savings_data = await self.fuel_savings_engine.async_get_stats()
            roi_data = await self.roi_engine.async_get_stats()
            return {
                "amber": amber_data,
                "arbitration": arbitration_data,
                "fuel_savings": fuel_savings_data,
                "roi": roi_data,
            }
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err!r}") from err
