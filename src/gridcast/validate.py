import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, train_test_split

from .model import fit_quantile_models


def _conformal_delta(models, X_cal: pd.DataFrame, y_cal: pd.Series, alpha: float) -> float:
    # CQR: additive adjustment (log space) giving a valid central (1 - alpha) interval.
    lower, upper = models[0.1].predict(X_cal), models[0.9].predict(X_cal)
    y_log = np.log1p(y_cal.to_numpy())
    scores = np.maximum(lower - y_log, y_log - upper)
    k = int(np.ceil((len(scores) + 1) * (1 - alpha)))
    return float(np.sort(scores)[min(k, len(scores)) - 1])


def _metrics(y_true, lo, med, hi) -> dict:
    abs_err = np.abs(y_true - med)
    return {
        "MAE": float(abs_err.mean()),
        "MedAE": float(np.median(abs_err)),
        "MAPE%": float((abs_err / np.clip(y_true, 1e-6, None)).mean() * 100),
        "cov%": float(((y_true >= lo) & (y_true <= hi)).mean() * 100),
    }


def cross_validate_by_group(X, y, groups, n_splits=5, alpha=0.2, random_state=0):
    # Each fold holds out whole regions; the interval is conformally calibrated on seen data.
    y_values = y.to_numpy()
    splitter = GroupKFold(n_splits=min(n_splits, groups.nunique()))
    out_of_fold = np.full(len(y_values), np.nan)
    rows = []
    for fold, (train_idx, test_idx) in enumerate(splitter.split(X, y_values, groups)):
        X_fit, X_cal, y_fit, y_cal = train_test_split(
            X.iloc[train_idx], y.iloc[train_idx], test_size=0.25, random_state=random_state
        )
        models = fit_quantile_models(X_fit, y_fit)
        delta = _conformal_delta(models, X_cal, y_cal, alpha)
        lo = np.expm1(models[0.1].predict(X.iloc[test_idx]) - delta)
        hi = np.expm1(models[0.9].predict(X.iloc[test_idx]) + delta)
        med = np.expm1(models[0.5].predict(X.iloc[test_idx]))
        out_of_fold[test_idx] = med
        held_out = ", ".join(sorted(groups.iloc[test_idx].unique()))
        rows.append({"fold": fold, "held_out": held_out[:24], "n": len(test_idx),
                     **_metrics(y_values[test_idx], lo, med, hi)})
    return pd.DataFrame(rows), out_of_fold
