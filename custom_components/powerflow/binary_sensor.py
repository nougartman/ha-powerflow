"""Binary sensor platform for Powerflow."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PowerflowCoordinator

_LOGGER = logging.getLogger(__name__)

BINARY_SENSOR_DESCRIPTIONS: list[BinarySensorEntityDescription] = [
    BinarySensorEntityDescription(
        key="solar_soak_predicted",
        name="Solar Soak Predicted",
        icon="mdi:solar-power-variant",
    ),
    BinarySensorEntityDescription(
        key="spike_warning_12h",
        name="Price Spike Warning (12h)",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:alert-circle-outline",
    ),
]

_KEY_MAP = {
    "solar_soak_predicted": ("amber", "solar_soak_predicted"),
    "spike_warning_12h":    ("amber", "spike_warning_12h"),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Powerflow binary sensor platform."""
    coordinator: PowerflowCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[PowerflowBinarySensor] = [
        PowerflowBinarySensor(coordinator, desc) for desc in BINARY_SENSOR_DESCRIPTIONS
    ]

    for vehicle in entry.data.get("vehicles", []):
        vid = vehicle["vehicle_id"]
        vname = vehicle.get("name", vid)
        entities.append(PowerflowBinarySensor(
            coordinator,
            BinarySensorEntityDescription(
                key=f"vehicle_{vid}_charge_desired",
                name=f"{vname} Charge Desired",
                icon="mdi:ev-station",
            ),
            vehicle_id=vid,
        ))

    async_add_entities(entities)


class PowerflowBinarySensor(CoordinatorEntity[PowerflowCoordinator], BinarySensorEntity):
    """Powerflow binary sensor entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PowerflowCoordinator,
        description: BinarySensorEntityDescription,
        vehicle_id: str | None = None,
    ) -> None:
        """Initialise binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._vehicle_id = vehicle_id
        self._attr_unique_id = f"{coordinator.entry_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return True if the condition is active."""
        if not self.coordinator.data:
            return None
        key = self.entity_description.key
        if self._vehicle_id:
            return bool(
                self.coordinator.data
                .get("arbitration", {})
                .get(self._vehicle_id, {})
                .get("charge_desired", False)
            )
        if key in _KEY_MAP:
            section, field = _KEY_MAP[key]
            return bool(self.coordinator.data.get(section, {}).get(field, False))
        return None
