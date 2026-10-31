from pathlib import Path

import numpy as np
import pandas as pd

from gridcast.benchmarks import SEGMENT_BENCHMARKS_KWH_MONTH

LOGS = Path("data/a2ei_skgs/A2EI_SKGS_data_release_April2022/skgs_data_LOGS_2021_82_systems.csv")


def a2ei_actual_kwh_month() -> pd.Series:
    raw = pd.read_csv(LOGS, usecols=["aam_id", "output_voltage_inv", "output_current_inv"])
    power = (raw["output_voltage_inv"].fillna(0) * raw["output_current_inv"].fillna(0)).clip(lower=0)
    mean_power = pd.DataFrame({"aam_id": raw["aam_id"], "power": power}).groupby("aam_id")["power"].mean()
    return mean_power * 730 / 1000


def main() -> None:
    actual = a2ei_actual_kwh_month()
    p10, p50, p90 = np.quantile(actual, [0.1, 0.5, 0.9])
    ours = SEGMENT_BENCHMARKS_KWH_MONTH["commercial"]

    print("Validation of the COMMERCIAL benchmark against 82 real metered A2EI systems:")
    print(f"  our benchmark (P10/P50/P90):  {ours[0]:.0f} / {ours[1]:.0f} / {ours[2]:.0f} kWh/month")
    print(f"  A2EI metered actual:          {p10:.0f} / {p50:.0f} / {p90:.0f} kWh/month")
    inside = ours[0] <= p50 <= ours[2]
    print(f"  A2EI median inside our P10-P90 band: {inside}")
    print("\nHousehold benchmark (3/7/18) vs metered references: Blodgett Kenya ~3.4, AMDA 2024 ~7.")
    print("A2EI are micro-enterprise solar generators, so they sit at the high end of 'commercial'.")


if __name__ == "__main__":
    main()
