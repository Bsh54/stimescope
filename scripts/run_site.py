from pathlib import Path

from gridcast.data import load_stevanato
from gridcast.model import fit_quantile_models
from gridcast.site import regional_error_ratios, site_demand

DATA = Path("data/stevanato_appliances/Database_ready_v2.csv")


def main() -> None:
    X, y, groups = load_stevanato(DATA)
    held = groups.value_counts().index[0]
    is_site = groups == held

    error_ratios = regional_error_ratios(X[~is_site], y[~is_site], groups[~is_site])
    median = fit_quantile_models(X[~is_site], y[~is_site])[0.5]
    estimate = site_demand(median, X[is_site], error_ratios, connection_rate=1.0)
    actual = float(y[is_site].sum())

    print(f"Held-out site = region {held}  ({int(is_site.sum())} households)")
    print(f"Predicted site demand  P10={estimate[0.1]:,.0f}  "
          f"P50={estimate[0.5]:,.0f}  P90={estimate[0.9]:,.0f} kWh/month")
    print(f"Actual site demand     {actual:,.0f} kWh/month")
    print(f"Actual within P10-P90 band: {estimate[0.1] <= actual <= estimate[0.9]}")


if __name__ == "__main__":
    main()
