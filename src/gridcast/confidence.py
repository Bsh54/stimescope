def confidence(n_buildings: int, source: str, n_anchor: int, per_customer_kwh: float,
               n_large: int = 0, osm_buildings: int | None = None) -> dict:
    # Transparent, lender-readable data-quality score; each factor states why confidence drops.
    score = 1.0
    reasons = []
    if source == "osm":
        score -= 0.20
        reasons.append("count from OSM only (undercounts rural); satellite footprints preferred")
    if n_buildings < 30:
        score -= 0.30
        reasons.append(f"very small settlement ({n_buildings} buildings): per-customer variance dominates")
    elif n_buildings < 100:
        score -= 0.10
        reasons.append(f"small settlement ({n_buildings} buildings)")
    if osm_buildings is not None and n_buildings >= 100 and osm_buildings < 0.2 * n_buildings:
        score -= 0.25
        reasons.append(f"OSM maps only {osm_buildings} of {n_buildings} structures here: businesses/anchors likely undercounted")
    if n_anchor == 0 and n_large > 0:
        score -= 0.10
        reasons.append(f"{n_large} large structures but no mapped anchors: productive use unverified")
    if not 5.0 <= per_customer_kwh <= 35.0:
        score -= 0.30
        reasons.append(f"per-customer demand {per_customer_kwh:.0f} kWh/mo outside the 5-35 range seen in the field")

    score = max(score, 0.0)
    level = "high" if score >= 0.8 else "medium" if score >= 0.5 else "low"
    return {"level": level, "score": round(score, 2), "reasons": reasons or ["all data-quality checks passed"]}
