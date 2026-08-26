"""Base interfaces for pricing providers."""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class PricingProvider(Protocol):
    """Protocol for pricing providers."""

    async def async_fetch_prices(self) -> dict:
        """Fetch current prices and forecast."""
        ...

    async def async_validate_credentials(self) -> bool:
        """Validate API credentials."""
        ...
