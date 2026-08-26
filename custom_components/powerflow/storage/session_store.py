"""Append-only JSONL session store for charging sessions."""
from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)
MAX_SESSIONS_PER_VEHICLE = 5000


class SessionStore:
    """Stores charging sessions as JSONL files under .storage/powerflow/."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialise store."""
        self._base_dir = Path(hass.config.path(".storage", "powerflow"))
        self._lock = asyncio.Lock()
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, vehicle_id: str) -> Path:
        return self._base_dir / f"{vehicle_id}.jsonl"

    async def async_append_session(self, session: dict[str, Any]) -> None:
        """Atomically append a session record."""
        vehicle_id = session.get("vehicle_id", "unknown")
        path = self._path(vehicle_id)
        line = json.dumps(session, separators=(",", ":")) + "\n"
        async with self._lock:
            await asyncio.to_thread(self._append_line, path, line)

    def _append_line(self, path: Path, line: str) -> None:
        tmp = path.with_suffix(".tmp")
        with open(tmp, "a", encoding="utf-8") as f:
            f.write(line)
        # Merge tmp into main file atomically
        if path.exists():
            with open(path, "a", encoding="utf-8") as f:
                f.write(line)
        else:
            os.replace(tmp, path)
        if tmp.exists():
            tmp.unlink(missing_ok=True)

    async def async_load_sessions(self, vehicle_id: str) -> list[dict[str, Any]]:
        """Load all sessions for a vehicle."""
        path = self._path(vehicle_id)
        if not path.exists():
            return []
        return await asyncio.to_thread(self._read_sessions, path)

    def _read_sessions(self, path: Path) -> list[dict[str, Any]]:
        sessions = []
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            sessions.append(json.loads(line))
                        except json.JSONDecodeError:
                            _LOGGER.warning("Skipping malformed session line in %s", path)
        except OSError as err:
            _LOGGER.error("Error reading sessions from %s: %s", path, err)
        return sessions[-MAX_SESSIONS_PER_VEHICLE:]
