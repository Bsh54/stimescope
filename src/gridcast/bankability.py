# IRR vs oversizing from CrossBoundary (30 kW mini-grid): 12.5% matched, 9.2% +50%, 6.1% +100%.
IRR_AT_MATCH = 12.5
IRR_LOSS_PER_OVERSIZE = 6.4


def irr_for_demand(planned_demand: float, actual_demand: float) -> float:
    oversize_ratio = max(planned_demand / max(actual_demand, 1e-9), 1.0)
    return IRR_AT_MATCH - IRR_LOSS_PER_OVERSIZE * (oversize_ratio - 1.0)


def bankability(demand_quantiles: dict, min_viable_irr: float = 6.0) -> tuple[dict, float]:
    # Size to P50; report the IRR if actual demand turns out at each quantile, and the demand
    # floor below which IRR falls under the viability threshold (the "how wrong before it fails").
    planned = demand_quantiles[0.5]
    irr = {q: irr_for_demand(planned, demand) for q, demand in demand_quantiles.items()}
    demand_floor = planned / (1 + (IRR_AT_MATCH - min_viable_irr) / IRR_LOSS_PER_OVERSIZE)
    return irr, demand_floor
