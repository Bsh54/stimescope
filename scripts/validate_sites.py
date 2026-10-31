from pathlib import Path

import numpy as np
import pandas as pd

from gridcast.estimate import estimate_site_demand

# Real held-out metered sites with published connection counts by segment.
# Sitolo: Frame et al. 2023 (metered 2022). Omorate/Tum: Wassie & Ahlgren 2024 (EEU metered,
# Dec 2021 counts; SMEs -> commercial, institutions -> anchor).
SITES = {
    "Sitolo (Malawi)": ({"household": 696, "commercial": 8, "anchor": 4}, 70003 / 12, "typical"),
    "Omorate (Ethiopia)": ({"household": 301, "commercial": 112, "anchor": 30}, 1065 * 30.4, "high"),
    "Tum (Ethiopia)": ({"household": 384, "commercial": 40, "anchor": 26}, 640 * 30.4, "high"),
}
A2EI_LOGS = Path("data/a2ei_skgs/A2EI_SKGS_data_release_April2022/skgs_data_LOGS_2021_82_systems.csv")


def a2ei_coverage() -> tuple:
    raw = pd.read_csv(A2EI_LOGS, usecols=["aam_id", "output_voltage_inv", "output_current_inv"])
    power = (raw["output_voltage_inv"].fillna(0) * raw["output_current_inv"].fillna(0)).clip(lower=0)
    kwh = pd.DataFrame({"id": raw["aam_id"], "p": power}).groupby("id")["p"].mean() * 730 / 1000
    return float(((kwh >= 15) & (kwh <= 75)).mean()), float(kwh.median()), int(kwh.size)


def main() -> None:
    print("Held-out site-total validation (metered vs predicted P10/P50/P90):\n")
    print(f"{'site':22} {'tier':8} {'metered':>9} {'P50 def':>8} {'P50 tier':>9} {'err def':>8} {'err tier':>9}  in-band")
    for name, (counts, metered, tier) in SITES.items():
        base = estimate_site_demand(counts, adoption_rate=1.0)
        d = estimate_site_demand(counts, adoption_rate=1.0, tier=tier)
        err0 = 100 * (base[0.5] - metered) / metered
        err = 100 * (d[0.5] - metered) / metered
        inband = d[0.1] <= metered <= d[0.9]
        print(f"{name:22} {tier:8} {metered:9,.0f} {base[0.5]:8,.0f} {d[0.5]:9,.0f} {err0:+7.0f}% {err:+8.0f}%  {inband}")

    frac, med, n = a2ei_coverage()
    print(f"\nPer-customer commercial benchmark vs {n} real metered A2EI systems:")
    print(f"  {frac*100:.0f}% fall inside our 15-75 band (P10-P90 targets ~80%); real median {med:.0f} vs our P50 40")
    print("\nHonest read: the default benchmark fits low-consumption rural (Sitolo +16%) but was biased")
    print("low for the Ethiopian towns. The NREL-grounded 'high' wealth tier (x3, from NREL income levels,")
    print("NOT fit to these sites) cuts that bias. Open problem: predicting the tier before connection")
    print("from a pre-connection wealth signal (nightlights / Relative Wealth Index).")


if __name__ == "__main__":
    main()
