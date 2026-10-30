import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

from .model import fit_quantile_models


def regional_error_ratios(X, y, groups, n_splits: int = 20) -> np.ndarray:
    # log(actual / predicted) of site totals across held-out regions = systematic site error.
    splitter = GroupKFold(n_splits=min(n_splits, groups.nunique()))
    ratios = []
    for train_idx, test_idx in splitter.split(X, y, groups):
        median = fit_quantile_models(X.iloc[train_idx], y.iloc[train_idx])[0.5]
        predicted = float(np.expm1(median.predict(X.iloc[test_idx])).sum())
        ratios.append(np.log(float(y.iloc[test_idx].sum()) / predicted))
    return np.array(ratios)


def site_demand(median_model, X_village: pd.DataFrame, error_ratios: np.ndarray,
                connection_rate: float = 1.0) -> dict:
    # The site range comes from the between-region error, which dominates household noise.
    predicted = float(np.expm1(median_model.predict(X_village)).sum()) * connection_rate
    lo, mid, hi = np.quantile(error_ratios, [0.1, 0.5, 0.9])
    return {0.1: predicted * np.exp(lo), 0.5: predicted * np.exp(mid), 0.9: predicted * np.exp(hi)}
