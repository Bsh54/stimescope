from pathlib import Path

import pandas as pd

TARGET = "Monthly_electricity_consumption"
GROUP = "Climate_zone_lev_1"

NUMERIC_FEATURES = [
    "Income_of_household",
    "Monthly_expenditure",
    "People_per_household",
    "Number_adults",
    "Number_youngsters",
    "Number_elderly",
    "Number_of_rooms",
    "Distance_from_grid",
    "Distance_from_city",
    "Population",
    "Relative_wealth_index_lev_3",
    "Relative_wealth_index_lev_2",
    "Population_density_lev_3",
    "Hours_available_electricity",
]


def load_stevanato(path: Path) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    df = pd.read_csv(path)
    y = pd.to_numeric(df[TARGET], errors="coerce")
    keep = y > 0
    df, y = df[keep].copy(), y[keep]

    appliance_cols = [c for c in df.columns if c.startswith(("Presence_", "m_"))]
    onehot_cols = [c for c in df.columns if c.startswith(("Connection_type_", "Urban/rural_"))]
    feature_cols = [c for c in NUMERIC_FEATURES if c in df.columns] + appliance_cols + onehot_cols

    X = df[feature_cols].apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all")
    groups = df[GROUP]
    valid = groups.notna()
    return X[valid], y[valid], groups[valid].astype(str)
