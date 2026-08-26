"""Arbitration engine for Powerflow."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant

from ..const import PRICE_DESCRIPTORS_CHEAP

_LOGGER = logging.getLogger(__name__)

MIN_SOLAR_EXCESS_KW = 1.2
PRIORITY_MAX_AMPS = 32
SECONDARY_MIN_AMPS = 6
OVERNIGHT_AMPS = 16


class ArbitrationEngine:
    """Decides charging mode based on Amber pricing, solar surplus, and SoC."""

    def __init__(self, hass: HomeAssistant, config_data: dict[str, Any]) -> None:
        """Initialise engine."""
        self.hass = hass
        self.vehicles = config_data.get("vehicles", [])
        self.rules = config_data.get("charging_rules", {})
        self.battery_soc_sensor = config_data.get("battery_soc_sensor")
        self.solar_sensor = config_data.get("solar_sensor")
        self.load_sensor = config_data.get("load_sensor")
        self.pw_capacity_kwh = float(config_data.get("pw_capacity_kwh", 13.5))

    def _get_state_float(self, entity_id: str | None, default: float = 0.0) -> float:
        """Safely read a HA state as float."""
        if not entity_id:
            return default
        state = self.hass.states.get(entity_id)
        if state and state.state not in ("unknown", "unavailable"):
            try:
                return float(state.state)
            except ValueError:
                pass
        return default

    def _parse_time(self, time_str: str) -> float:
        """Parse HH:MM to fractional hours."""
        try:
            hh, mm = time_str.split(":")
            return int(hh) + int(mm) / 60.0
        except (ValueError, AttributeError):
            return 0.0

    def _in_window(self, t: datetime, start_str: str, end_str: str) -> bool:
        """Check if time t falls within window (supports overnight spans)."""
        current = t.hour + t.minute / 60.0
        start = self._parse_time(start_str)
        end = self._parse_time(end_str)
        if start <= end:
            return start <= current < end
        return current >= start or current < end

    async def async_evaluate(self, amber_data: dict) -> dict:
        """Evaluate charging strategy for all configured vehicles."""
        if not self.vehicles or not amber_data:
            return {}

        now = datetime.now()
        solar_kw = self._get_state_float(self.solar_sensor)
        load_kw = self._get_state_float(self.load_sensor)
        battery_soc = self._get_state_float(self.battery_soc_sensor, default=100.0)
        solar_excess_kw = max(0.0, solar_kw - load_kw)

        descriptor = amber_data.get("descriptor", "neutral")
        spike_status = amber_data.get("spike_status", "none")
        solar_soak_predicted = amber_data.get("solar_soak_predicted", False)

        is_peak = spike_status in ("potential", "spike") or descriptor == "spike"
        is_peak |= self._in_window(now, self.rules.get("peak_morning_start", "06:00"), self.rules.get("peak_morning_end", "09:00"))
        is_peak |= self._in_window(now, self.rules.get("peak_evening_start", "17:00"), self.rules.get("peak_evening_end", "21:00"))

        is_solar_soak = (
            solar_soak_predicted
            and descriptor in PRICE_DESCRIPTORS_CHEAP
            and solar_excess_kw >= MIN_SOLAR_EXCESS_KW
        )
        is_overnight = self._in_window(
            now,
            self.rules.get("overnight_start", "00:00"),
            self.rules.get("overnight_end", "06:00"),
        )

        charge_desired = False
        target_amps = 0
        reason = "Idle"

        if is_peak:
            charge_desired = False
            reason = "Peak Lockout"
        elif is_solar_soak:
            charge_desired = True
            target_amps = PRIORITY_MAX_AMPS
            reason = "Solar Soak"
        elif is_overnight:
            charge_desired = True
            target_amps = OVERNIGHT_AMPS
            reason = "Overnight"
        elif descriptor in PRICE_DESCRIPTORS_CHEAP:
            charge_desired = True
            target_amps = OVERNIGHT_AMPS
            reason = "Cheap Rate"

        results = {}
        amps_remaining = target_amps

        for idx, vehicle in enumerate(self.vehicles):
            vid = vehicle["vehicle_id"]
            if idx == 0:
                v_amps = min(PRIORITY_MAX_AMPS, amps_remaining)
            else:
                v_amps = amps_remaining if amps_remaining >= SECONDARY_MIN_AMPS else 0

            v_charge = charge_desired and v_amps > 0
            amps_remaining = max(0, amps_remaining - v_amps)

            results[vid] = {
                "charge_desired": v_charge,
                "target_amps": v_amps,
                "reason": f"{reason} (amps: {v_amps}A)",
            }

        return results
