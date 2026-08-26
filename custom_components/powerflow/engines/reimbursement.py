"""Reimbursement engine for novated lease charging sessions."""
from __future__ import annotations

import csv
import io
import logging
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant

from ..storage.session_store import SessionStore

_LOGGER = logging.getLogger(__name__)

MAX_SESSION_KWH = 85
MIN_SOC_DELTA = 1


class ReimbursementEngine:
    """Computes novated lease reimbursement per billing cycle."""

    def __init__(self, hass: HomeAssistant, config_data: dict[str, Any]) -> None:
        """Initialise engine."""
        self.hass = hass
        self.config = config_data
        self.session_store = SessionStore(hass)

    def get_billing_cycle_boundaries(self, now: datetime) -> tuple[datetime, datetime]:
        """Return (start, end) of the current monthly billing cycle."""
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            end = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            end = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, end

    def _is_valid_session(self, session: dict) -> bool:
        """Apply anomaly and phantom session guards."""
        added = session.get("energy_added_kwh", 0.0)
        if added > MAX_SESSION_KWH or added < 0:
            _LOGGER.warning("Skipping anomalous session: kWh=%.2f", added)
            return False
        start_soc = session.get("starting_soc", 0)
        end_soc = session.get("ending_soc", 0)
        if end_soc - start_soc < MIN_SOC_DELTA:
            _LOGGER.debug("Skipping phantom session: SoC delta=%d%%", end_soc - start_soc)
            return False
        return True

    async def async_get_current_cycle_stats(self, vehicle_id: str) -> dict:
        """Get current billing cycle stats for a vehicle."""
        now = datetime.now()
        start, end = self.get_billing_cycle_boundaries(now)
        sessions = await self.session_store.async_load_sessions(vehicle_id)

        grid_kwh = 0.0
        solar_kwh = 0.0
        total_kwh = 0.0
        grid_cost = 0.0

        for s in sessions:
            try:
                s_time = datetime.fromisoformat(s.get("ended_at", ""))
                if s_time.tzinfo is not None:
                    s_time = s_time.replace(tzinfo=None)
            except ValueError:
                continue

            if not (start <= s_time < end):
                continue
            if not self._is_valid_session(s):
                continue

            added = float(s.get("energy_added_kwh", 0.0))
            grid_fraction = float(s.get("grid_fraction", 0.5))
            total_kwh += added
            grid_kwh += added * grid_fraction
            solar_kwh += added * (1.0 - grid_fraction)
            grid_cost += float(s.get("grid_cost", 0.0))

        return {
            "grid_kwh": round(grid_kwh, 3),
            "solar_kwh": round(solar_kwh, 3),
            "total_kwh": round(total_kwh, 3),
            "grid_cost": round(grid_cost, 2),
            "reimbursement_due": round(grid_cost, 2),
        }

    async def async_export_csv(self, vehicle_id: str, start_date: datetime, end_date: datetime) -> str:
        """Export a CSV of charging sessions for novated lease reimbursement."""
        sessions = await self.session_store.async_load_sessions(vehicle_id)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date", "Energy Added (kWh)", "Grid (kWh)", "Solar (kWh)", "Cost ($)"])

        for s in sessions:
            try:
                s_time = datetime.fromisoformat(s.get("ended_at", ""))
                if s_time.tzinfo is not None:
                    s_time = s_time.replace(tzinfo=None)
            except ValueError:
                continue
            if not (start_date <= s_time <= end_date):
                continue
            if not self._is_valid_session(s):
                continue

            added = float(s.get("energy_added_kwh", 0.0))
            grid_fraction = float(s.get("grid_fraction", 0.5))
            writer.writerow([
                s_time.strftime("%Y-%m-%d %H:%M:%S"),
                f"{added:.3f}",
                f"{added * grid_fraction:.3f}",
                f"{added * (1 - grid_fraction):.3f}",
                f"{float(s.get('grid_cost', 0.0)):.2f}",
            ])

        return output.getvalue()
