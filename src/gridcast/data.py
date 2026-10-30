from pathlib import Path

import pandas as pd

TARGET = "Monthly_electricity_consumption"
GROUP = "Climate_zone_lev_1"

# Only pre-connection signals: an unelectrified village has no appliances, hours, or tariff yet.
PRE_CONNECTION_NUMERIC = [
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
    "Relative_wealth_index_lev_2",
    "Relative_wealth_index_lev_3",
    "Population_density_lev_2",
    "Population_density_lev_3",
    "Price_candles",
    "Price_kerosene",
    "Price_charcoal",
    "Price_LPG",
    "Price_firewood",
    "Land_owned",
    "Dwelling_quality_index",
    "Age_HHH",
    "Years_of_HHH_in_community",
    "Size_of_business_employees",
    "Size_of_business_revenues",
]

PRE_CONNECTION_ONEHOT = (
    "Urban/rural_",
    "House_ownership_rental_free_",
    "Male/female_HHH_",
    "Marital_status_HHH_",
    "Socio_status_HHH_",
    "Type_of_business_",
)


def load_stevanato(path: Path) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    df = pd.read_csv(path)
    y = pd.to_numeric(df[TARGET], errors="coerce")
    mask = (y > 0) & (y <= y[y > 0].quantile(0.99))
    df, y = df[mask].copy(), y[mask]

    numeric = [c for c in PRE_CONNECTION_NUMERIC if c in df.columns]
    onehot = [c for c in df.columns if c.startswith(PRE_CONNECTION_ONEHOT)]
    X = df[numeric + onehot].apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all")

    groups = df[GROUP]
    valid = groups.notna()
    return X[valid], y[valid], groups[valid].astype(str)
