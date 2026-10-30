import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split

from .model import fit_quantile_models


def driver_importance(X: pd.DataFrame, y: pd.Series, top: int = 12,
                      n_repeats: int = 5, random_state: int = 0) -> pd.DataFrame:
    # Importance = how much the median prediction worsens (log-MAE) when a feature is shuffled.
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=random_state)
    median = fit_quantile_models(X_tr, y_tr)[0.5]
    result = permutation_importance(
        median, X_te, np.log1p(y_te.to_numpy()),
        scoring="neg_mean_absolute_error", n_repeats=n_repeats, random_state=random_state,
    )
    table = pd.DataFrame({"feature": X.columns, "importance": result.importances_mean})
    return table.sort_values("importance", ascending=False).head(top).reset_index(drop=True)
