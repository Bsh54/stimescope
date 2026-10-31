import numpy as np

from .benchmarks import SEGMENT_BENCHMARKS_KWH_MONTH, lognormal_params


def segment_medians(segment_counts: dict, adoption_rate: float = 0.7) -> dict:
    out = {}
    for segment, count in segment_counts.items():
        connected = count if segment == "anchor" else count * adoption_rate
        out[segment] = connected * SEGMENT_BENCHMARKS_KWH_MONTH[segment][1]
    return out


def estimate_site_demand(segment_counts: dict, adoption_rate: float = 0.7,
                         n_sims: int = 20000, random_state: int = 0) -> dict:
    # Bottom-up: a village-level per-customer level is drawn once per simulation from the
    # real metered benchmark (systematic uncertainty dominates), then summed over segments.
    rng = np.random.default_rng(random_state)
    totals = np.zeros(n_sims)
    for segment, count in segment_counts.items():
        mu, sigma = lognormal_params(*SEGMENT_BENCHMARKS_KWH_MONTH[segment])
        level = rng.lognormal(mu, sigma, n_sims)
        connected = count if segment == "anchor" else count * adoption_rate
        totals += connected * level
    return {q: float(np.quantile(totals, q)) for q in (0.1, 0.5, 0.9)}
