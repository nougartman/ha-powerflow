"""HA Store-backed persistence for Powerflow cumulative data."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from ..const import DOMAIN, STORAGE_VERSION

_LOGGER = logging.getLogger(__name__)
_STORE_KEY = f"{DOMAIN}.data"


class PowerflowStore:
    """Persistent key-value store backed by HA storage."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialise store."""
        self._store: Store = Store(hass, STORAGE_VERSION, _STORE_KEY)
        self._lock = asyncio.Lock()

    async def async_load(self) -> dict[str, Any]:
        """Load data from store, returning empty dict if nothing saved yet."""
        data = await self._store.async_load()
        return data or {}

    async def async_save(self, data: dict[str, Any]) -> None:
        """Atomically save data to HA storage."""
        async with self._lock:
            await self._store.async_save(data)

    async def async_update_vehicle(self, vehicle_id: str, delta: dict[str, Any]) -> None:
        """Merge delta into the stored data for a vehicle."""
        async with self._lock:
            data = await self.async_load()
            vehicle_data = data.get(vehicle_id, {})
            vehicle_data.update(delta)
            data[vehicle_id] = vehicle_data
            await self._store.async_save(data)
