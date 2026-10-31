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
4. **Aggregate deterministically** with a connection rate, summing the segments'
   lognormal demand bands (Fenton-Wilkinson: match mean and variance, refit one
   lognormal) to a site P10/P50/P90. No random draws: identical inputs give
   identical outputs.
5. **Project the growth curve** derived from real A2EI smart-meter telemetry and
   the Wassie metered trajectory (demand roughly triples over the first ~5 months,
   then grows ~30%/yr through year 2).
6. **Check bankability**: map the demand range to project IRR (CrossBoundary
   sensitivity) and report how far below forecast demand can fall before the
   project stops clearing a viable IRR.

## Validation

The commercial benchmark is checked against 82 real metered A2EI systems (our
P10/P50/P90 band contains the metered median). The growth curve is derived
directly from that same telemetry. Household benchmarks track Blodgett (~3.4) and
AMDA (~7) metered references.

## Reproduce

The engine is deterministic and needs no external data. From a clean clone:

```
pip install -e .
python scripts/validate_sites.py     # held-out metered validation (below)
python scripts/run_estimate.py       # demand + growth for a sample site
```

`validate_sites.py` prints, identically on every run and machine:

```
site                   tier        RWI   metered  P50 tier  err def  err tier  in-band
Sitolo (Malawi)        typical   -0.32     5,834     6,817     +17%      +17%  True
Omorate (Ethiopia)     high      -0.40    32,376    31,812     -51%       -2%  True
Tum (Ethiopia)         high      -0.32    19,456    22,692     -38%      +17%  True
```

The three metered totals fall inside the predicted P10-P90 at all sites. The RWI
column and the A2EI benchmark line use datasets that are not bundled (see
`data/README.md`); when absent the script falls back to the published values so
the core validation still runs with zero downloads.

## Frontend

`gridcast.engine.js` is a byte-faithful JavaScript port of the Python engine; it
runs the whole demand pipeline offline in the browser. A cross-check of the two
engines on 4 sites and 92 numeric fields shows 0 difference. The web app
(`code.html`) calls a small FastAPI service only for the satellite building count
(the Open Buildings tiles are too large for a browser); all demand math is client
side.

Run the app offline (no server, demo + custom sites, full engine):

```
python -m http.server 8000 --directory web   # then open http://localhost:8000/code.html
```

Live satellite counts additionally need the count service:

```
pip install fastapi uvicorn
GRIDCAST_HOME=/path/with/tiles uvicorn server.gridcast_api:app --port 8611
```

The Open Buildings tiles it indexes are public (CC-BY, storage.googleapis.com/
open-buildings-data) and downloaded on demand per country.

## Layout

- `src/gridcast/` — package source (benchmarks, estimate, growth, loadprofile,
  sizing, bankability, confidence, geo, open_buildings, wealth) + `growth_curve.csv`
- `scripts/` — command-line entry points, incl. `validate_sites.py`
- `web/` — offline web app + JavaScript engine; `server/` — count service
- `data/` — datasets (not committed; see `data/README.md`)

## Status

Global Energy Hackathon 2026 sprint.
