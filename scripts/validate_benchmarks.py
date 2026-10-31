from pathlib import Path

import numpy as np
import pandas as pd

from gridcast.benchmarks import SEGMENT_MEDIAN_KWH_MONTH

LOGS = Path("data/a2ei_skgs/A2EI_SKGS_data_release_April2022/skgs_data_LOGS_2021_82_systems.csv")


def a2ei_actual_kwh_month() -> pd.Series:
    raw = pd.read_csv(LOGS, usecols=["aam_id", "output_voltage_inv", "output_current_inv"])
    power = (raw["output_voltage_inv"].fillna(0) * raw["output_current_inv"].fillna(0)).clip(lower=0)
    mean_power = pd.DataFrame({"aam_id": raw["aam_id"], "power": power}).groupby("aam_id")["power"].mean()
    return mean_power * 730 / 1000


def main() -> None:
    actual = a2ei_actual_kwh_month()
    p25, p50, p75 = np.quantile(actual, [0.25, 0.5, 0.75])
    ours = SEGMENT_MEDIAN_KWH_MONTH["commercial"]

    print("Commercial per-customer median vs 82 real metered A2EI micro-enterprises:")
    print(f"  our commercial median:  {ours:.0f} kWh/month")
    print(f"  A2EI metered (P25/P50/P75): {p25:.0f} / {p50:.0f} / {p75:.0f} kWh/month")
    print("\nA2EI are micro-enterprise solar generators (high end of 'commercial'); our 22 is the")
    print("rural-village central. Household median 4 tracks Blodgett Kenya ~3.4 and the MDPI 2026 set.")


if __name__ == "__main__":
    main()
