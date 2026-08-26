"""Sensor platform for Powerflow."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PowerflowCoordinator

_LOGGER = logging.getLogger(__name__)

SENSOR_DESCRIPTIONS: list[SensorEntityDescription] = [
    SensorEntityDescription(
        key="amber_current_price",
        name="Current Electricity Price",
        native_unit_of_measurement="AUD/kWh",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=4,
    ),
    SensorEntityDescription(
        key="amber_feed_in_price",
        name="Feed-in Tariff",
        native_unit_of_measurement="AUD/kWh",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=4,
    ),
    SensorEntityDescription(
        key="amber_descriptor",
        name="Price Descriptor",
    ),
    SensorEntityDescription(
        key="amber_forecast_12h_min",
        name="12h Forecast Min Price",
        native_unit_of_measurement="AUD/kWh",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=4,
    ),
    SensorEntityDescription(
        key="amber_forecast_12h_max",
        name="12h Forecast Max Price",
        native_unit_of_measurement="AUD/kWh",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=4,
    ),
    SensorEntityDescription(
        key="amber_forecast_12h_avg",
        name="12h Forecast Avg Price",
        native_unit_of_measurement="AUD/kWh",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=4,
    ),
    SensorEntityDescription(
        key="fleet_fuel_savings",
        name="Fleet Fuel Savings",
        native_unit_of_measurement="AUD",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="fleet_petrol_avoided",
        name="Fleet Petrol Avoided",
        native_unit_of_measurement="L",
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="fleet_distance_tracked",
        name="Fleet Distance Tracked",
        native_unit_of_measurement="km",
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="local_e91_fuel_price",
        name="Local ULP91 Fuel Price",
        native_unit_of_measurement="AUD/L",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
    ),
    SensorEntityDescription(
        key="roi_total_saved",
        name="ROI Total Saved",
        native_unit_of_measurement="AUD",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="roi_payback_percent",
        name="ROI Payback Progress",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key="roi_payback_remaining",
        name="ROI Remaining",
        native_unit_of_measurement="AUD",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key="roi_monthly_avg",
        name="ROI Monthly Average Savings",
        native_unit_of_measurement="AUD",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
]

_KEY_MAP = {
    "amber_current_price":    ("amber", "current_price"),
    "amber_feed_in_price":    ("amber", "feed_in_price"),
    "amber_descriptor":       ("amber", "descriptor"),
    "amber_forecast_12h_min": ("amber", "forecast_12h_min"),
    "amber_forecast_12h_max": ("amber", "forecast_12h_max"),
    "amber_forecast_12h_avg": ("amber", "forecast_12h_avg"),
    "fleet_fuel_savings":     ("fuel_savings", "fleet_fuel_savings"),
    "fleet_petrol_avoided":   ("fuel_savings", "fleet_petrol_avoided"),
    "fleet_distance_tracked": ("fuel_savings", "fleet_distance_tracked"),
    "local_e91_fuel_price":   ("fuel_savings", "local_e91_fuel_price"),
    "roi_total_saved":        ("roi", "total_saved"),
    "roi_payback_percent":    ("roi", "payback_percent"),
    "roi_payback_remaining":  ("roi", "payback_remaining_dollars"),
    "roi_monthly_avg":        ("roi", "monthly_savings_avg"),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Powerflow sensor platform."""
    coordinator: PowerflowCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[PowerflowSensor] = [PowerflowSensor(coordinator, desc) for desc in SENSOR_DESCRIPTIONS]

    for vehicle in entry.data.get("vehicles", []):
        vid = vehicle["vehicle_id"]
        vname = vehicle.get("name", vid)
        entities.append(PowerflowSensor(
            coordinator,
            SensorEntityDescription(
                key=f"vehicle_{vid}_target_amps",
                name=f"{vname} Target Amps",
                native_unit_of_measurement="A",
                state_class=SensorStateClass.MEASUREMENT,
            ),
            vehicle_id=vid,
            data_key="target_amps",
        ))
        entities.append(PowerflowSensor(
            coordinator,
            SensorEntityDescription(
                key=f"vehicle_{vid}_reason",
                name=f"{vname} Charge Reason",
            ),
            vehicle_id=vid,
            data_key="reason",
        ))

    async_add_entities(entities)


class PowerflowSensor(CoordinatorEntity[PowerflowCoordinator], SensorEntity):
    """Powerflow sensor entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PowerflowCoordinator,
        description: SensorEntityDescription,
        vehicle_id: str | None = None,
        data_key: str | None = None,
    ) -> None:
        """Initialise sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._vehicle_id = vehicle_id
        self._data_key = data_key
        self._attr_unique_id = f"{coordinator.entry_id}_{description.key}"

    @property
    def native_value(self) -> float | str | None:
        """Return sensor state."""
        if not self.coordinator.data:
            return None
        key = self.entity_description.key
        if self._vehicle_id and self._data_key:
            return (
                self.coordinator.data
                .get("arbitration", {})
                .get(self._vehicle_id, {})
                .get(self._data_key)
            )
        if key in _KEY_MAP:
            section, field = _KEY_MAP[key]
            return self.coordinator.data.get(section, {}).get(field)
        return None
