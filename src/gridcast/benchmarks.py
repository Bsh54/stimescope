import math

# Median per-customer demand (kWh/month) by segment, grounded in metered references:
# household  -> Blodgett Kenya mini-grids ~3.4, MDPI 2026 harmonized existing median ~3.9
# commercial -> AMDA benchmarking average ~26, A2EI metered; conservative central 22
# anchor     -> productive loads (mill, cold storage, telecom), central 180
SEGMENT_MEDIAN_KWH_MONTH = {"household": 4.0, "commercial": 22.0, "anchor": 180.0}

# Wealth-tier multiplier on household/commercial medians (NREL income levels Low/Med/High).
WEALTH_TIER = {"low": 0.5, "typical": 1.0, "high": 3.0}

# Cross-site demand spread as a lognormal sigma, calibrated on 38 metered African microgrids
# (Ajasse et al. 2026, Zenodo 21324726): leave-one-country-out P10-P90 coverage ~80%. This is the
# honest "demand varies several-fold before building" uncertainty, the dominant one.
SITE_LOG_SIGMA = 1.4

_Z90 = 1.2815515655446004
