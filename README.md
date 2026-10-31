# gridcast

Pre-connection electricity demand estimation for mini-grids.

`gridcast` estimates the electricity demand of an unelectrified community
*before* a mini-grid is built — as a calibrated range (P10 / P50 / P90), not a
single number — together with a post-connection growth curve and a bankability
check. It runs on open public data alone, from a pair of coordinates.

Built for the Global Energy Hackathon 2026, Problem Brief 03 —
"Predict mini-grid demand before building" (Digital Solutions & AI).

## Why it matters

Developers size systems and raise financing from demand forecasts. Unelectrified
villages have no meter history, and surveys mislead because people cannot predict
use of electricity they have never had. Forecasts can be off several-fold, which
leads to oversized systems with unaffordable tariffs, undersized systems that
brown out, or projects that never get financed.

## Approach

A regression on existing consumption is the wrong tool here: the only open
household consumption data is from *grid-connected* homes, a different and much
higher-demand population than a new rural mini-grid serves. `gridcast` instead
uses the sector-standard **bottom-up** method (e-GUIDE / VIDA):

1. **Count customers** from satellite building footprints (Google Open Buildings,
   with OSM as a fallback) within a radius of the site.
2. **Segment** them into households, commercial, and anchor (productive) loads.
3. **Apply per-customer demand benchmarks** taken from *real metered* references
   (Blodgett Kenya mini-grids, AMDA, A2EI telemetry), each as a P10/P50/P90 band.
4. **Aggregate by Monte Carlo** with an adoption rate, propagating the systematic
   between-site uncertainty that dominates demand (≈ several-fold), to a site
   P10/P50/P90.
5. **Project the growth curve** derived from real A2EI smart-meter telemetry
   (demand roughly triples over the first ~5 months, then plateaus).
6. **Check bankability**: map the demand range to project IRR (CrossBoundary
   sensitivity) and report how far below forecast demand can fall before the
   project stops clearing a viable IRR.

## Validation

The commercial benchmark is checked against 82 real metered A2EI systems (our
P10/P50/P90 band contains the metered median). The growth curve is derived
directly from that same telemetry. Household benchmarks track Blodgett (~3.4) and
AMDA (~7) metered references.

## Layout

- `src/gridcast/` — package source (benchmarks, estimate, growth, geo,
  open_buildings, bankability)
- `scripts/` — command-line entry points
- `data/` — datasets (not committed; see `data/README.md`)

## Status

Global Energy Hackathon 2026 sprint.
