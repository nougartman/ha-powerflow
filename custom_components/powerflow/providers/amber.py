"""Amber Electric API provider with full 48-interval forecast."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant

from ..const import AMBER_API_BASE, AMBER_FORECAST_INTERVALS, PRICE_DESCRIPTORS_CHEAP

_LOGGER = logging.getLogger(__name__)


class AmberProvider:
    """Fetches pricing and 48-interval forecast from the Amber Electric API."""

    def __init__(self, hass: HomeAssistant, config_data: dict[str, Any]) -> None:
        """Initialise provider."""
        self.hass = hass
        self._api_key = config_data.get("amber_api_key", "")
        self._site_id = config_data.get("site_id", "")
        self._pv_sensor = config_data.get("pv_forecast_sensor")

    async def async_validate_credentials(self) -> bool:
        """Return True if the API key and site ID are accepted by Amber."""
        try:
            await self.async_fetch_prices()
            return True
        except Exception:  # noqa: BLE001
            return False

    async def async_fetch_prices(self) -> dict:
        """Fetch current + 48-interval forecast from Amber API."""
        url = f"{AMBER_API_BASE}/sites/{self._site_id}/prices/current"
        params = {"next": str(AMBER_FORECAST_INTERVALS), "previous": "0"}
        headers = {"Authorization": f"Bearer {self._api_key}", "Accept": "application/json"}

        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params, headers=headers) as resp:
                resp.raise_for_status()
                intervals = await resp.json()

        return self._parse_intervals(intervals)

    def _parse_intervals(self, intervals: list[dict]) -> dict:
        """Parse the raw Amber interval list into a structured data dict."""
        current_price: float = 0.0
        feed_in_price: float = 0.0
        descriptor: str = "neutral"
        spike_status: str = "none"
        forecast_general: list[float] = []
        spike_warning_12h: bool = False
        solar_soak_predicted: bool = False

        for interval in intervals:
            channel = interval.get("channelType", "")
            itype = interval.get("type", "")
            per_kwh = interval.get("perKwh", 0)

            # Convert c/kWh to $/kWh if value looks like cents
            price = float(per_kwh) / 100.0 if abs(float(per_kwh)) > 2 else float(per_kwh)

            if channel == "feedIn":
                if itype == "CurrentInterval":
                    feed_in_price = price
                continue

            if channel != "general":
                continue

            if itype == "CurrentInterval":
                current_price = price
                descriptor = interval.get("descriptor", "neutral")
                spike_status = interval.get("spikeStatus", "none")
            elif itype == "ForecastInterval":
                forecast_general.append(price)
                if interval.get("spikeStatus") == "spike" or interval.get("descriptor") == "spike":
                    spike_warning_12h = True
                if interval.get("descriptor") in PRICE_DESCRIPTORS_CHEAP:
                    solar_soak_predicted = True

        forecast_12h = forecast_general[:24]  # 24 x 30-min = 12 hours

        # Check PV forecast sensor for solar soak confirmation
        if self._pv_sensor:
            state = self.hass.states.get(self._pv_sensor)
            if state and state.state not in ("unknown", "unavailable"):
                try:
                    pv_remaining = float(state.state)
                    solar_soak_predicted = solar_soak_predicted and pv_remaining > 2.0
                except ValueError:
                    pass

        return {
            "current_price": round(current_price, 5),
            "feed_in_price": round(feed_in_price, 5),
            "descriptor": descriptor,
            "spike_status": spike_status,
            "forecast_12h_min": round(min(forecast_12h, default=current_price), 5),
            "forecast_12h_max": round(max(forecast_12h, default=current_price), 5),
            "forecast_12h_avg": round(sum(forecast_12h) / len(forecast_12h), 5) if forecast_12h else current_price,
            "spike_warning_12h": spike_warning_12h,
            "solar_soak_predicted": solar_soak_predicted,
        }
