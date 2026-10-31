from pathlib import Path

import numpy as np
import pandas as pd

from gridcast.estimate import estimate_site_demand

# Real held-out metered sites with published connection counts by segment.
# Sitolo: Frame et al. 2023 (metered 2022). Omorate/Tum: Wassie & Ahlgren 2024 (EEU metered,
# Dec 2021 counts; SMEs -> commercial, institutions -> anchor).
SITES = {
    "Sitolo (Malawi)": ({"household": 696, "commercial": 8, "anchor": 4}, 70003 / 12),
    "Omorate (Ethiopia)": ({"household": 301, "commercial": 112, "anchor": 30}, 1065 * 30.4),
    "Tum (Ethiopia)": ({"household": 384, "commercial": 40, "anchor": 26}, 640 * 30.4),
}
A2EI_LOGS = Path("data/a2ei_skgs/A2EI_SKGS_data_release_April2022/skgs_data_LOGS_2021_82_systems.csv")


def a2ei_coverage() -> tuple:
    raw = pd.read_csv(A2EI_LOGS, usecols=["aam_id", "output_voltage_inv", "output_current_inv"])
    power = (raw["output_voltage_inv"].fillna(0) * raw["output_current_inv"].fillna(0)).clip(lower=0)
    kwh = pd.DataFrame({"id": raw["aam_id"], "p": power}).groupby("id")["p"].mean() * 730 / 1000
    return float(((kwh >= 15) & (kwh <= 75)).mean()), float(kwh.median()), int(kwh.size)


def main() -> None:
    print("Held-out site-total validation (metered vs predicted P10/P50/P90):\n")
    print(f"{'site':22} {'metered':>9} {'P10':>7} {'P50':>7} {'P90':>7} {'P50 err':>8}  in-band")
    for name, (counts, metered) in SITES.items():
        d = estimate_site_demand(counts, adoption_rate=1.0)
        err = 100 * (d[0.5] - metered) / metered
        inband = d[0.1] <= metered <= d[0.9]
        print(f"{name:22} {metered:9,.0f} {d[0.1]:7,.0f} {d[0.5]:7,.0f} {d[0.9]:7,.0f} {err:+7.0f}%  {inband}")

    frac, med, n = a2ei_coverage()
    print(f"\nPer-customer commercial benchmark vs {n} real metered A2EI systems:")
    print(f"  {frac*100:.0f}% fall inside our 15-75 band (P10-P90 targets ~80%); real median {med:.0f} vs our P50 40")
    print("\nHonest read: our P10-P90 band contains the metered total at all three sites, but P50 is")
    print("biased low for higher-consumption towns (Omorate/Tum). The benchmark is calibrated to")
    print("low-consumption rural (Blodgett/AMDA/Sitolo, 5-35 kWh/customer); Ethiopian towns sit higher.")


if __name__ == "__main__":
    main()
