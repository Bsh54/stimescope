import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

QUANTILES = (0.1, 0.5, 0.9)


DEFAULT_PARAMS = {
    "max_iter": 500,
    "learning_rate": 0.05,
    "min_samples_leaf": 30,
    "l2_regularization": 0.1,
}


def fit_quantile_models(X: pd.DataFrame, y: pd.Series, quantiles=QUANTILES, random_state=0, params=None):
    # Train in log space so skewed consumption and the quantile ordering stay stable.
    settings = {**DEFAULT_PARAMS, **(params or {})}
    y_log = np.log1p(y.to_numpy())
    models = {}
    for q in quantiles:
        model = HistGradientBoostingRegressor(loss="quantile", quantile=q,
                                              random_state=random_state, **settings)
        model.fit(X, y_log)
        models[q] = model
    return models


def predict_quantiles(models, X: pd.DataFrame) -> dict[float, np.ndarray]:
    return {q: np.expm1(model.predict(X)) for q, model in models.items()}
