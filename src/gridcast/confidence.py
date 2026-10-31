def confidence(n_buildings: int, source: str, n_anchor: int, per_customer_kwh: float,
               n_large: int = 0, osm_buildings: int | None = None) -> dict:
    # Grounded in the held-out validation (scripts/validate_sites.py): the P10-P90 band contained
    # the metered total at all 3 sites, but the P50 point estimate was accurate (+16%) only where
    # per-customer demand sat in the validated 5-35 kWh band, and biased low (-37 to -50%) for
    # higher-consumption towns. Confidence here rates the POINT estimate, not the band.
    score = 1.0
    reasons = []
    if not 5.0 <= per_customer_kwh <= 35.0:
        score -= 0.40
        reasons.append(f"implied {per_customer_kwh:.0f} kWh/customer is outside the 5-35 band our P50 is validated on; expect P50 bias, trust the range")
    if source == "open_buildings":
        score -= 0.25
        reasons.append("automatic satellite estimate: buildings are a ceiling, not connections (our 3 metered sites ran 1.6x-14x more buildings than connections); set planned connections and wealth tier for a validated figure")
    if source == "osm":
        score -= 0.20
        reasons.append("count from OSM only (undercounts rural); satellite footprints preferred")
    if osm_buildings is not None and n_buildings >= 100 and osm_buildings < 0.2 * n_buildings:
        score -= 0.25
        reasons.append(f"OSM maps only {osm_buildings} of {n_buildings} structures, so the business/anchor share is a guess (field range 2-25%)")
    if n_buildings < 30:
        score -= 0.30
        reasons.append(f"very small settlement ({n_buildings} buildings): per-customer variance dominates")
    elif n_buildings < 100:
        score -= 0.10
        reasons.append(f"small settlement ({n_buildings} buildings)")
    if n_anchor == 0 and n_large > 0:
        score -= 0.10
        reasons.append(f"{n_large} large structures but no mapped anchors: productive use unverified")

    score = max(score, 0.0)
    level = "high" if score >= 0.8 else "medium" if score >= 0.5 else "low"
    return {"level": level, "score": round(score, 2), "reasons": reasons or ["resembles the validated low-consumption rural sites"]}
