import numpy as np

from .benchmarks import SEGMENT_BENCHMARKS_KWH_MONTH, WEALTH_TIER, lognormal_params


def _tier_factor(segment: str, tier: str) -> float:
    return 1.0 if segment == "anchor" else WEALTH_TIER[tier]


def segment_medians(segment_counts: dict, adoption_rate: float = 0.7, tier: str = "typical") -> dict:
    out = {}
    for segment, count in segment_counts.items():
        connected = count if segment == "anchor" else count * adoption_rate
        out[segment] = connected * SEGMENT_BENCHMARKS_KWH_MONTH[segment][1] * _tier_factor(segment, tier)
    return out


def estimate_site_demand(segment_counts: dict, adoption_rate: float = 0.7, tier: str = "typical",
                         n_sims: int = 20000, random_state: int = 0) -> dict:
    # Bottom-up: a village-level per-customer level is drawn once per simulation from the real
    # metered benchmark (systematic uncertainty dominates), scaled by wealth tier, summed over segments.
    rng = np.random.default_rng(random_state)
    totals = np.zeros(n_sims)
    for segment, count in segment_counts.items():
        mu, sigma = lognormal_params(*SEGMENT_BENCHMARKS_KWH_MONTH[segment])
        level = rng.lognormal(mu, sigma, n_sims) * _tier_factor(segment, tier)
        connected = count if segment == "anchor" else count * adoption_rate
        totals += connected * level
    return {q: float(np.quantile(totals, q)) for q in (0.1, 0.5, 0.9)}
