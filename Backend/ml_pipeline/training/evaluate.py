"""Model metrics used by retraining promotion gates."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def regression_metrics(y_true, y_pred) -> dict[str, float]:
    actual = np.asarray(y_true, dtype=float)
    predicted = np.asarray(y_pred, dtype=float)
    if len(actual) == 0 or not np.isfinite(actual).all() or not np.isfinite(predicted).all():
        raise ValueError("Evaluation requires finite, non-empty targets and predictions")
    errors = actual - predicted
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)) if len(actual) > 1 else 0.0,
        "median_absolute_error": float(np.median(np.abs(errors))),
    }


def quantile_metrics(y_true, predictions: dict[float, np.ndarray]) -> dict[str, float]:
    actual = np.asarray(y_true, dtype=float)
    result: dict[str, float] = {}
    for quantile, values in predictions.items():
        values = np.asarray(values, dtype=float)
        error = actual - values
        result[f"quantile_loss_{quantile:g}"] = float(
            np.mean(np.maximum(quantile * error, (quantile - 1) * error))
        )
    if 0.1 in predictions and 0.9 in predictions:
        lower, upper = predictions[0.1], predictions[0.9]
        result["p10_p90_coverage"] = float(np.mean((actual >= lower) & (actual <= upper)))
        result["interval_width"] = float(np.mean(upper - lower))
    return result
