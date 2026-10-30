# Data

Raw datasets are not committed (see `.gitignore`). Download them into the
matching subfolder below.

## Sources

- **Kenya MTF** (Multi-Tier Framework) household energy survey — ESMAP / World
  Bank, CC BY 4.0. Raw `.dta` files plus codebook.
  https://energydata.info/dataset/kenya-multi-tier-framework-mtf-survey
  -> `kenya_mtf/`
- **Rwanda MTF 2022** (households, public institutions, mini-grids) — World Bank
  microdata. https://microdata.worldbank.org/index.php/catalog/6429
- **Building footprints** — Google Open Buildings; OpenStreetMap.
- **Nighttime lights** — NOAA VIIRS.
- **Grid lines** — GridFinder.
- **Settlements and services** — Energy Access Explorer.
- **Metered mini-grid references** — Blodgett et al. 2017 (eight Kenya sites),
  Wassie & Ahlgren 2024 (Ethiopia), PowerGen / A2EI (Tanzania).

## Acquired (local, not committed)

- `kenya_mtf/` — Kenya MTF survey. 4590 households, 777 variables; target
  `c_c_21` electricity consumption (kWh/month). CC BY 4.0.
- `stevanato_appliances/` — Harmonized multi-source appliance/consumption database
  (Stevanato et al., Zenodo 7185210). 7765 rows, 223 columns: income, relative
  wealth index, distance to grid/city, connection type, appliance presence and
  counts, monthly electricity consumption. CC BY 4.0.
- `ethiopia_chalmers/` — Ethiopia solar mini-grid impact survey (Mendeley
  tvhr5pbmdz). 464 households, intervention (connected) vs control (not
  electrified); income, appliances, monthly electricity expenditure.
- `minigrid_projects_104/` — 104 renewable mini-grid projects (Mendeley
  s3wm2sgjjb). Site level: country, ownership, technology, kW sizes, storage,
  success flag.
- `a2ei_skgs/` — A2EI "Solar Killed the Generator Star" release (82 systems,
  Nigeria). Metadata with lat/lon + PV/battery/inverter sizing, plus
  `skgs_data_LOGS...csv` real metered time series (kept zipped until needed).

## Layout

- `kenya_mtf/` — Kenya MTF survey (raw `.dta`, codebook, questionnaire).
