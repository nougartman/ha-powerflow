# Powerflow ⚡🔋

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![CI](https://github.com/nougartman/ha-powerflow/actions/workflows/ci.yml/badge.svg)](https://github.com/nougartman/ha-powerflow/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Powerflow** is a Home Assistant custom integration that acts as an advanced solar + EV charging arbitration engine. It optimises when and how fast your Tesla charges based on Amber Electric pricing, solar excess, and Powerwall state — using the full 48-interval 24h forecast API that the official Amber integration does not expose.

---

## Why Powerflow?

The official Amber HA integration only shows the **current 30-minute interval**. Powerflow calls the Amber API with `?next=48` to get the full 24-hour forecast, enabling:

- Predictive **Solar Soak** window detection (charge hardest when your panels will produce most)
- **Overnight cheap window** scheduling
- **12-hour price spike warnings** so the Powerwall isn't depleted before an evening peak
- Dynamic **Powerwall pacing reserve** — adjusts the reserve target every cycle to hit 100% by your chosen hour

---

## Prerequisites

- **Amber Electric** account & API key ([app.amber.com.au](https://app.amber.com.au))
- **Tesla Vehicle** controlled via [Tessie](https://tessie.com) or the official Tesla HA integration
- *(Optional)* **Solcast** or **Forecast.Solar** for PV forecasting — auto-detected on setup

---

## Installation via HACS

1. Open **HACS** → **Integrations**
2. Click ⋮ → **Custom repositories**
3. Add `https://github.com/nougartman/ha-powerflow` as category **Integration**
4. Install **Powerflow** and restart Home Assistant

---

## Configuration

Go to **Settings** → **Devices & Services** → **Add Integration** → search **Powerflow**.

Follow the 5-step setup wizard:

| Step | Purpose |
|------|---------|
| 1 | Amber Electric API key + Site ID — validated live against the API |
| 2 | Solar, load & grid power sensors + battery / Powerwall type |
| 3 | Vehicle profiles (up to 4) — Tessie or official Tesla integration |
| 4 | Charging rules: peak windows, overnight SoC limits, solar soak window |
| 5 | Solar ROI tracker + fuel price source (NSW/ACT FuelCheck, HA sensor, manual) |

---

## Sensors Created

| Entity | Description |
|--------|-------------|
| `sensor.powerflow_amber_current_price` | Live Amber price ($/kWh) |
| `sensor.powerflow_amber_forecast_12h_min` | 12h forecast minimum price |
| `sensor.powerflow_amber_forecast_12h_max` | 12h forecast maximum price |
| `sensor.powerflow_fleet_fuel_savings` | Total EV vs ICE fuel savings (AUD) |
| `sensor.powerflow_fleet_petrol_avoided` | Petrol avoided (L) |
| `sensor.powerflow_roi_total_saved` | Total solar/battery ROI saved (AUD) |
| `sensor.powerflow_roi_payback_percent` | Payback progress (%) |
| `sensor.powerflow_local_e91_fuel_price` | Local ULP91 price (AUD/L) |
| `binary_sensor.powerflow_solar_soak_predicted` | Solar soak window predicted today |
| `binary_sensor.powerflow_spike_warning_12h` | Price spike forecast in next 12h |
| `sensor.powerflow_{vehicle}_target_amps` | Per-vehicle target charge current |
| `binary_sensor.powerflow_{vehicle}_charge_desired` | Per-vehicle charge command |

---

## Services

| Service | Description |
|---------|-------------|
| `powerflow.start_charge` | Wake and start charging a vehicle |
| `powerflow.stop_charge` | Stop charging a vehicle |
| `powerflow.set_charge_current` | Set charge amps (6–32A) |
| `powerflow.log_away_charge` | Manually log a public/away charging session |
| `powerflow.export_reimbursement_csv` | Export novated lease CSV for current billing cycle |
| `powerflow.recalculate_fuel_savings` | Force coordinator refresh |

---

## Features

### Smart Arbitration Engine
Evaluates charging strategy every 5 minutes based on:
- Amber price descriptor (`extremelyLow`, `low`, `neutral`, `high`, `spike`)
- Spike status in the 12-hour forecast
- Solar excess power available right now
- Time-of-day windows (configurable peak, overnight, solar soak)

### Dual-Vehicle Support
Up to 4 vehicles, balanced across available amperage — priority vehicle gets `PRIORITY_MAX_AMPS`, secondary gets the remainder (min 6A or nothing).

### Fuel Savings Engine
Tracks EV charging cost vs equivalent ICE petrol cost per vehicle and fleet. Fuel price is sourced via a 5-tier strategy:
1. Manual override
2. HA sensor
3. NSW/ACT FuelCheck API (live ULP91)
4. Quarterly historical average (national fallback)
5. Internal hardcoded last-known value

### Solar ROI Tracker
Tracks cumulative savings against install cost and projects payback timeline based on monthly average savings rate.

### Novated Lease Reimbursement
Records each charging session (grid kWh, solar kWh, cost), filters phantom sessions, and exports a CSV for employer reimbursement claims.

---

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md).

## License
MIT © 2026 nougartman
