from pathlib import Path

import numpy as np

from gridcast.data import load_stevanato
from gridcast.validate import cross_validate_by_group

DATA = Path("data/stevanato_appliances/Database_ready_v2.csv")


def main() -> None:
    X, y, groups = load_stevanato(DATA)
    print(f"rows={len(X)}  features={X.shape[1]}  groups={groups.nunique()}  "
          f"median_actual={y.median():.1f} kWh/month")

    results, out_of_fold = cross_validate_by_group(X, y, groups)
    print("\nHeld-out validation (each fold predicts on unseen regions):")
    print(results.to_string(index=False))

    mask = ~np.isnan(out_of_fold)
    err = np.abs(y.to_numpy()[mask] - out_of_fold[mask])
    print(f"\nOverall held-out: MAE={err.mean():.1f}  MedAE={np.median(err):.1f} kWh/month "
          f"(median actual {y.median():.1f})  |  mean P10-P90 coverage={results['cov%'].mean():.0f}%")


if __name__ == "__main__":
    main()
