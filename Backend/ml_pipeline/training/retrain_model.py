"""Train quantile groundwork only when genuine ScrapMonster history is sufficient."""

from __future__ import annotations

import argparse
import json
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline

from ..etl.pipeline_config import (
    FEATURE_SCHEMA_PATH, FEATURES_DIR, MIN_SCRAP_HISTORY_DAYS, MIN_TRAINING_ROWS,
    MODEL_REGISTRY_DIR, RANDOM_SEED,
)
from ..etl.trainable import FEATURE_COLUMNS, TARGET, build_trainable_dataset
from ..etl.validation import chronological_split
from .evaluate import quantile_metrics, regression_metrics
from .model_registry import new_version_dir, write_active_pointer


def _quantile_model(quantile: float):
    return make_pipeline(
        SimpleImputer(strategy="median", add_indicator=True),
        HistGradientBoostingRegressor(
            loss="quantile", quantile=quantile, random_state=RANDOM_SEED,
            max_iter=150, learning_rate=0.05, max_leaf_nodes=15,
        ),
    )


def retrain() -> dict[str, Any]:
    result = build_trainable_dataset()
    data = result["dataset"]
    dates = pd.to_datetime(data["observation_date"], errors="coerce")
    genuine_dates = int(dates.dropna().dt.date.nunique())
    eligible = data[data["is_trainable"].fillna(False)].copy()
    if genuine_dates < MIN_SCRAP_HISTORY_DAYS or len(eligible) < MIN_TRAINING_ROWS:
        return {
            "status": "skipped",
            "reason": "insufficient_scrapmonster_history",
            "collection_dates": genuine_dates,
            "minimum_collection_dates": MIN_SCRAP_HISTORY_DAYS,
            "eligible_rows": int(len(eligible)),
            "minimum_training_rows": MIN_TRAINING_ROWS,
        }
    splits = chronological_split(eligible)
    numeric = [column for column in FEATURE_COLUMNS if column in splits["train"]]
    x_train, y_train = splits["train"][numeric], splits["train"][TARGET]
    x_val, y_val = splits["validation"][numeric], splits["validation"][TARGET]
    models = {}
    predictions = {}
    for quantile in (0.1, 0.5, 0.9):
        model = _quantile_model(quantile)
        model.fit(x_train, y_train)
        models[quantile] = model
        predictions[quantile] = model.predict(x_val)
    # Enforce ordered intervals at inference/evaluation boundaries.
    ordered = np.sort(np.column_stack([predictions[0.1], predictions[0.5], predictions[0.9]]), axis=1)
    metrics = {
        "p50": regression_metrics(y_val, ordered[:, 1]),
        "quantiles": quantile_metrics(y_val, {0.1: ordered[:, 0], 0.5: ordered[:, 1], 0.9: ordered[:, 2]}),
        "train_rows": len(splits["train"]), "validation_rows": len(splits["validation"]),
        "test_rows": len(splits["test"]), "feature_columns": numeric,
    }
    version = f"v{pd.Timestamp.utcnow():%Y%m%d%H%M%S}"
    directory = new_version_dir(version)
    for quantile, model in models.items():
        joblib.dump(model, directory / f"model_p{int(quantile * 100)}.joblib")
    directory.joinpath("metadata.json").write_text(json.dumps({
        "version": version, "target": TARGET, "quantiles": [0.1, 0.5, 0.9],
        "dataset_path": result["path"], "genuine_collection_dates": genuine_dates,
    }, indent=2), encoding="utf-8")
    directory.joinpath("feature_schema.json").write_text(
        FEATURE_SCHEMA_PATH.read_text(encoding="utf-8"), encoding="utf-8"
    )
    directory.joinpath("metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_active_pointer(version, directory)
    return {"status": "promoted", "version": version, "metrics": metrics}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    try:
        print(json.dumps(retrain(), indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
