"""Constants for the Powerflow integration."""
from __future__ import annotations

DOMAIN = "powerflow"
PLATFORMS = ["sensor", "binary_sensor"]

# Config keys
CONF_AMBER_API_KEY = "amber_api_key"
CONF_SITE_ID = "site_id"
CONF_SOLAR_SENSOR = "solar_sensor"
CONF_LOAD_SENSOR = "load_sensor"
CONF_GRID_SENSOR = "grid_sensor"
CONF_BATTERY_TYPE = "battery_type"
CONF_BATTERY_SOC_SENSOR = "battery_soc_sensor"
CONF_PW_CAPACITY_KWH = "pw_capacity_kwh"
CONF_TARGET_FULL_HOUR = "target_full_hour"
CONF_PV_FORECAST_SENSOR = "pv_forecast_sensor"
CONF_VEHICLES = "vehicles"
CONF_CHARGING_RULES = "charging_rules"
CONF_INSTALL_COST = "install_cost"
CONF_INSTALL_DATE = "install_date"
CONF_CARRY_IN_SAVINGS = "carry_in_savings"
CONF_NOVATED_LEASE = "novated_lease"
CONF_FUEL_PRICE_SOURCE = "fuel_price_source"
CONF_FUEL_PRICE_MANUAL = "fuel_price_manual"
CONF_NSW_FUELCHECK_KEY = "nsw_fuelcheck_key"

# Battery Types
BATTERY_TYPE_TESSIE = "tessie_powerwall"
BATTERY_TYPE_OFFICIAL = "official_powerwall"
BATTERY_TYPE_GENERIC = "generic_sensor"
BATTERY_TYPE_NONE = "none"

# Vehicle Integration Types
VEHICLE_INTEGRATION_TESSIE = "tessie"
VEHICLE_INTEGRATION_OFFICIAL = "official_tesla"

# Fuel Sources
FUEL_SOURCE_MANUAL = "manual"
FUEL_SOURCE_HA_SENSOR = "ha_sensor"
FUEL_SOURCE_NSW_FUELCHECK = "nsw_fuelcheck"
FUEL_SOURCE_QUARTERLY_AVG = "quarterly_avg"

# Price Descriptors
PRICE_DESCRIPTORS_CHEAP = {"negative", "extremelyLow", "veryLow", "low"}

# API Endpoints
AMBER_API_BASE = "https://api.amber.com.au/v1"
NSW_FUELCHECK_API_BASE = "https://api.nsw.gov.au/FuelCheckApp/v1/fuel/prices"

# Defaults & Constants
AMBER_FORECAST_INTERVALS = 48
DEFAULT_PW_CAPACITY_KWH = 13.5
DEFAULT_TARGET_FULL_HOUR = 15.0
DEFAULT_MAX_GRID_KW = 18.0
DEFAULT_OVERNIGHT_SOC_LIMIT = 40
STORAGE_VERSION = 1
STORAGE_KEY = "powerflow"

# Historical ULP91 prices (AUD/L) by quarter — national fallback
HISTORICAL_ULP91_PRICE: dict[str, float] = {
    "2024-Q1": 2.08, "2024-Q2": 2.12, "2024-Q3": 2.05, "2024-Q4": 1.98,
    "2025-Q1": 2.10, "2025-Q2": 2.15, "2025-Q3": 2.08, "2025-Q4": 2.02,
    "2026-Q1": 2.09, "2026-Q2": 2.14, "2026-Q3": 2.11,
}
