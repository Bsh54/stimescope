import math

from .benchmarks import SEGMENT_BENCHMARKS_KWH_MONTH, WEALTH_TIER, lognormal_params

Z90 = 1.2815515655446004


def _tier_factor(segment: str, tier: str) -> float:
    return 1.0 if segment == "anchor" else WEALTH_TIER[tier]


def segment_medians(segment_counts: dict, adoption_rate: float = 0.7, tier: str = "typical") -> dict:
    out = {}
    for segment, count in segment_counts.items():
        connected = count if segment == "anchor" else count * adoption_rate
        out[segment] = connected * SEGMENT_BENCHMARKS_KWH_MONTH[segment][1] * _tier_factor(segment, tier)
    return out


def estimate_site_demand(segment_counts: dict, adoption_rate: float = 0.7, tier: str = "typical") -> dict:
    # Deterministic sum of independent scaled lognormals (Fenton-Wilkinson): match mean+variance,
    # refit one lognormal, read P10/P50/P90. The per-segment level carries systematic uncertainty.
    mean = variance = 0.0
    for segment, count in segment_counts.items():
        base_mu, sigma = lognormal_params(*SEGMENT_BENCHMARKS_KWH_MONTH[segment])
        mu = base_mu + math.log(_tier_factor(segment, tier))
        s2 = sigma * sigma
        n = count if segment == "anchor" else count * adoption_rate
        mean += n * math.exp(mu + s2 / 2)
        variance += n * n * (math.exp(s2) - 1) * math.exp(2 * mu + s2)
    if mean <= 0:
        return {0.1: 0.0, 0.5: 0.0, 0.9: 0.0}
    sig2 = math.log(1 + variance / (mean * mean))
    mu_sum = math.log(mean) - sig2 / 2
    sig_sum = math.sqrt(sig2)
    return {0.1: math.exp(mu_sum - Z90 * sig_sum), 0.5: math.exp(mu_sum), 0.9: math.exp(mu_sum + Z90 * sig_sum)}
