import math

from .benchmarks import SEGMENT_MEDIAN_KWH_MONTH, WEALTH_TIER, SITE_LOG_SIGMA, _Z90


def _tier_factor(segment: str, tier: str) -> float:
    return 1.0 if segment == "anchor" else WEALTH_TIER[tier]


def segment_medians(segment_counts: dict, adoption_rate: float = 0.7, tier: str = "typical") -> dict:
    out = {}
    for segment, count in segment_counts.items():
        connected = count if segment == "anchor" else count * adoption_rate
        out[segment] = connected * SEGMENT_MEDIAN_KWH_MONTH[segment] * _tier_factor(segment, tier)
    return out


def estimate_site_demand(segment_counts: dict, adoption_rate: float = 0.7, tier: str = "typical") -> dict:
    # Central estimate is bottom-up (customers x metered per-customer medians x tier); the P10-P90
    # band is the measured cross-site spread (SITE_LOG_SIGMA), which dominates before connection.
    p50 = sum(segment_medians(segment_counts, adoption_rate, tier).values())
    if p50 <= 0:
        return {0.1: 0.0, 0.5: 0.0, 0.9: 0.0}
    return {0.1: p50 * math.exp(-_Z90 * SITE_LOG_SIGMA), 0.5: p50, 0.9: p50 * math.exp(_Z90 * SITE_LOG_SIGMA)}
