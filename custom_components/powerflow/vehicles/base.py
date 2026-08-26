"""Abstract base class for vehicle controllers."""
from __future__ import annotations

from abc import ABC, abstractmethod


class VehicleController(ABC):
    """Abstract interface for controlling a Tesla vehicle."""

    @abstractmethod
    async def async_wake(self) -> None:
        """Wake the vehicle."""

    @abstractmethod
    async def async_start_charge(self) -> None:
        """Start charging."""

    @abstractmethod
    async def async_stop_charge(self) -> None:
        """Stop charging."""

    @abstractmethod
    async def async_set_charge_current(self, amps: int) -> None:
        """Set charging current in amps."""
