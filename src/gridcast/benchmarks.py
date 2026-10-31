import numpy as np

# Per-customer demand (kWh/month) as (P10, P50, P90), grounded in real metered references:
# household  -> Blodgett Kenya mini-grids ~3.4, AMDA residential ~7
# commercial -> A2EI metered IQR ~30-68 (median 52), AMDA commercial ~26
# anchor     -> productive loads (mill, cold storage, telecom), highly variable
SEGMENT_BENCHMARKS_KWH_MONTH = {
    "household": (3.0, 7.0, 18.0),
    "commercial": (15.0, 40.0, 75.0),
    "anchor": (80.0, 250.0, 800.0),
}

# Wealth tier multiplier on household/commercial levels, grounded in NREL's income-differentiated
# rural SSA household demand (Low 3.3 / Medium 9.2 / High 21.5 kWh/month); typical = our default.
WEALTH_TIER = {"low": 0.5, "typical": 1.0, "high": 3.0}

_Z90 = 1.2815515655446004


def lognormal_params(p10: float, p50: float, p90: float) -> tuple[float, float]:
    mu = np.log(p50)
    sigma = (np.log(p90) - np.log(p10)) / (2 * _Z90)
    return mu, sigma
