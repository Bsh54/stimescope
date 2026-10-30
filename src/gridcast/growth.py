from pathlib import Path

import pandas as pd

_COLUMNS = ["aam_id", "timestamp_utc", "output_voltage_inv", "output_current_inv"]


def growth_curve(logs_path: Path, min_systems: int = 30) -> pd.DataFrame:
    # Fraction of mature demand by month since connection, from real A2EI telemetry.
    raw = pd.read_csv(logs_path, usecols=_COLUMNS)
    power = (raw["output_voltage_inv"].fillna(0) * raw["output_current_inv"].fillna(0)).clip(lower=0)
    daily = pd.DataFrame({"aam_id": raw["aam_id"], "date": raw["timestamp_utc"].str[:10], "power_w": power})
    daily = daily.groupby(["aam_id", "date"])["power_w"].mean().reset_index()
    daily["date"] = pd.to_datetime(daily["date"])
    age_days = daily["date"] - daily.groupby("aam_id")["date"].transform("min")
    daily["month"] = age_days.dt.days // 30

    table = daily.groupby("month").agg(wh_day=("power_w", lambda s: s.median() * 24),
                                       n_systems=("aam_id", "nunique"))
    table = table[table["n_systems"] >= min_systems]
    table["fraction_of_mature"] = (table["wh_day"] / table["wh_day"].max()).round(3)
    return table[["fraction_of_mature", "n_systems"]]


def project_demand(mature_estimate: dict, curve: pd.DataFrame) -> pd.DataFrame:
    rows = {month: {q: value * fraction for q, value in mature_estimate.items()}
            for month, fraction in curve["fraction_of_mature"].items()}
    return pd.DataFrame(rows).T
