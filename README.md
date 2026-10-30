# gridcast

Pre-connection electricity demand estimation for mini-grids.

`gridcast` estimates the electricity demand of an unelectrified community
*before* a mini-grid is built — as a calibrated range (P10 / P50 / P90), not a
single number — together with a multi-year growth curve and a plain-language
explanation of the drivers. Estimates are validated against held-out metered
sites and run on open public data alone.

Built for the Global Energy Hackathon 2026, Problem Brief 03 —
"Predict mini-grid demand before building" (Digital Solutions & AI).

## Why it matters

Developers size systems and raise financing from demand forecasts. Unelectrified
villages have no meter history, and surveys mislead because people cannot predict
use of electricity they have never had. Forecasts can be off several-fold, which
leads to oversized systems with unaffordable tariffs, undersized systems that
brown out, or projects that never get financed.

## Approach

- Features from open geospatial and survey data: building footprints, nighttime
  lights, distance to grid, settlements and services, and household energy
  surveys (World Bank Multi-Tier Framework).
- A transparent model that returns a demand range per customer and per site,
  plus a growth curve for the first years after connection.
- Validation against held-out metered mini-grid sites.
- Driver explanations a lender can review.

## Layout

- `src/gridcast/` — package source
- `scripts/` — command-line entry points
- `tests/` — tests
- `data/` — datasets (not committed; see `data/README.md`)

## Status

Early work, Global Energy Hackathon 2026 sprint.
