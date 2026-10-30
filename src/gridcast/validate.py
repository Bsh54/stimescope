import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

from .model import fit_quantile_models, predict_quantiles


def _fold_metrics(y_true: np.ndarray, preds: dict[float, np.ndarray]) -> dict:
    median = preds[0.5]
    abs_err = np.abs(y_true - median)
    mae = float(abs_err.mean())
    mape = float((abs_err / np.clip(y_true, 1e-6, None)).mean() * 100)
    coverage = float(((y_true >= preds[0.1]) & (y_true <= preds[0.9])).mean() * 100)
    return {"MAE": mae, "MAPE%": mape, "P10_P90_cov%": coverage}


def cross_validate_by_group(X: pd.DataFrame, y: pd.Series, groups: pd.Series, n_splits: int = 5):
    # Each fold holds out whole groups (regions): a proxy for predicting on unseen sites.
    y_values = y.to_numpy()
    splitter = GroupKFold(n_splits=min(n_splits, groups.nunique()))
    out_of_fold = np.full(len(y_values), np.nan)
    rows = []
    for fold, (train_idx, test_idx) in enumerate(splitter.split(X, y_values, groups)):
        models = fit_quantile_models(X.iloc[train_idx], y.iloc[train_idx])
        preds = predict_quantiles(models, X.iloc[test_idx])
        metrics = _fold_metrics(y_values[test_idx], preds)
        out_of_fold[test_idx] = preds[0.5]
        held_out = ", ".join(sorted(groups.iloc[test_idx].unique()))
        rows.append({"fold": fold, "held_out": held_out[:32], "n_test": len(test_idx), **metrics})
    return pd.DataFrame(rows), out_of_fold
