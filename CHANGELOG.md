# Changelog

All notable changes to Powerflow will be documented here.
This project follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Semantic Versioning](https://semver.org/).

---

## [1.0.0] - 2026-08-26

### Added
- Initial release of the Powerflow HACS custom integration
- **Amber Electric direct REST API client** — calls `?next=48` for the full 24h / 48-interval forecast (the official HA Amber integration only exposes the current 30-minute interval)
- **EV charging arbitration engine** with three modes:
  - Solar Soak (max amps when solar excess ≥ 1.2 kW and price is cheap)
  - Overnight cheap-rate window (configurable, default 00:00–06:00)
  - Peak lockout (morning and evening peak windows + spike detection)
- **Dynamic Powerwall pacing reserve** — adjusts reserve target each cycle to hit 100% by your chosen hour
- **Fleet fuel savings tracker** — compares EV charging cost vs ICE equivalent per vehicle and fleet-wide
- **Novated lease reimbursement calculator** with CSV export for employer claims
- **Solar/battery ROI tracker** — tracks payback progress and projects timeline
- **Tessie vehicle controller** — auto-reads token from existing Tessie HA integration config entry
- **Official Tesla HA integration controller** — uses `tesla_custom` service domain
- **5-step config flow** — Amber credentials, solar/battery sensors, vehicle profiles, charging rules, ROI & fuel price
- **NSW/ACT FuelCheck API** fuel price source with 5-tier fallback strategy
- **Per-vehicle and fleet sensor entities** exposed as standard HA sensors and binary sensors
- `services.yaml` with selectors for all 6 Powerflow services
- English translations (`translations/en.json`)
- GitHub Actions CI (PR-only) and release validation workflows
- MIT licence
