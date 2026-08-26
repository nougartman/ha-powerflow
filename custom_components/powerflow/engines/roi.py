"""ROI engine for Powerflow."""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

from homeassistant.core import HomeAssistant

from ..const import CONF_INSTALL_COST, CONF_INSTALL_DATE, CONF_CARRY_IN_SAVINGS

_LOGGER = logging.getLogger(__name__)

SAVINGS_SENSOR_CANDIDATES = [
    "sensor.powerflow_solar_pure_usage_savings_accumulative",
    "sensor.solar_savings_total",
    "sensor.energy_savings_total",
]


class ROIEngine:
    """Tracks solar/battery ROI and payback progress."""

    def __init__(self, hass: HomeAssistant, config_data: dict[str, Any]) -> None:
        """Initialise ROI engine."""
        self.hass = hass
        self.config = config_data

    def _read_savings_sensor(self) -> float:
        """Auto-detect accumulated savings from HA states."""
        for sensor_id in SAVINGS_SENSOR_CANDIDATES:
            state = self.hass.states.get(sensor_id)
            if state and state.state not in ("unknown", "unavailable"):
                try:
                    return float(state.state)
                except ValueError:
                    pass
        return 0.0

    async def async_get_stats(self) -> dict:
        """Calculate and return ROI statistics."""
        install_cost = float(self.config.get(CONF_INSTALL_COST, 0.0))
        carry_in = float(self.config.get(CONF_CARRY_IN_SAVINGS, 0.0))
        install_date_str = self.config.get(CONF_INSTALL_DATE)

        savings_sensor_value = self._read_savings_sensor()
        total_saved = carry_in + savings_sensor_value
        payback_percent = (total_saved / install_cost * 100.0) if install_cost > 0 else 100.0
        payback_remaining = max(0.0, install_cost - total_saved)

        monthly_avg = 0.0
        if install_date_str and total_saved > 0:
            try:
                install_dt = date.fromisoformat(install_date_str)
                months_elapsed = (
                    (datetime.now().year - install_dt.year) * 12
                    + datetime.now().month - install_dt.month
                )
                if months_elapsed > 0:
                    monthly_avg = total_saved / months_elapsed
            except (ValueError, OverflowError):
                pass

        return {
            "install_cost": install_cost,
            "install_date": install_date_str,
            "carry_in_savings": carry_in,
            "total_saved": round(total_saved, 2),
            "payback_percent": round(payback_percent, 1),
            "payback_remaining_dollars": round(payback_remaining, 2),
            "monthly_savings_avg": round(monthly_avg, 2),
        }
