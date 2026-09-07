"""
ScrapLink — Sprint 2
Baseline Price Recommendation Model Training Script
====================================================
Trains two models on the engineered commodity feature matrix:
  1. Linear Regression  — simple baseline benchmark
  2. XGBoost Regressor  — Sprint 2 deliverable model

Usage:
    # From Backend/ directory:
    python ml_pipeline/train_price_model.py

Outputs:
    ml_pipeline/models/linear_regression_baseline.pkl
    ml_pipeline/models/xgboost_price_model.pkl
    ml_pipeline/models/preprocessor.pkl
    ml_pipeline/models/label_encoder.pkl
    ml_pipeline/models/evaluation_report.json
"""

import os
import sys
import json
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor

# ─────────────────────────────────────────────────────────────────────────────
# Path Setup
# ─────────────────────────────────────────────────────────────────────────────
SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
DATA_DIR      = os.path.join(SCRIPT_DIR, "data")
RAW_DIR       = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
REPORTS_DIR   = os.path.join(DATA_DIR, "reports")
MODELS_DIR    = os.path.join(SCRIPT_DIR, "models")

FEATURE_CSV   = os.path.join(PROCESSED_DIR, "engineered_commodity_features.csv")
PROCESSED_CSV = os.path.join(PROCESSED_DIR, "merged_commodity_prices.csv")
RAW_CSV       = os.path.join(RAW_DIR, "raw_commodity_prices.csv")

os.makedirs(MODELS_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Step 0: Run ETL pipeline if processed data is missing
# ─────────────────────────────────────────────────────────────────────────────
def ensure_data():
    """Runs the Sprint 1 ETL pipeline if the feature CSV does not exist yet."""
    if os.path.exists(FEATURE_CSV):
        print(f"[DATA] Feature matrix found: {FEATURE_CSV}")
        return

    print("[DATA] Feature matrix not found. Running ETL pipeline...")
    if SCRIPT_DIR not in sys.path:
        sys.path.insert(0, SCRIPT_DIR)

    from etl.scrapers import generate_full_historical_dataset
    from etl.ingest   import clean_and_ingest_data
    from etl.eda      import perform_eda
    from etl.features import engineer_features

    raw_csv       = generate_full_historical_dataset(RAW_DIR)
    processed_csv = clean_and_ingest_data(raw_csv, PROCESSED_DIR)
    perform_eda(processed_csv, REPORTS_DIR)
    engineer_features(processed_csv, PROCESSED_DIR)

    if not os.path.exists(FEATURE_CSV):
        raise FileNotFoundError(f"ETL pipeline ran but feature CSV still missing: {FEATURE_CSV}")
    print(f"[DATA] ETL complete. Feature matrix ready: {FEATURE_CSV}")


# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Load & Prepare Features
# ─────────────────────────────────────────────────────────────────────────────
FEATURE_COLS = [
    "commodity_encoded",
    "lag_1",
    "lag_7",
    "lag_14",
    "lag_30",
    "rolling_mean_7",
    "rolling_mean_30",
    "rolling_std_7",
    "rolling_std_30",
    "pct_change_7",
    "pct_change_30",
]
TARGET_COL = "spot_price_inr_kg"


def load_and_prepare(feature_csv: str):
    """Loads the engineered feature CSV and prepares X, y with encoding."""
    print(f"\n[LOAD] Reading feature matrix from: {feature_csv}")
    df = pd.read_csv(feature_csv)
    print(f"  Shape          : {df.shape[0]:,} rows x {df.shape[1]} columns")
    print(f"  Commodities    : {sorted(df['commodity'].unique())}")
    print(f"  Date range     : {df['date'].min()} to {df['date'].max()}")

    le = LabelEncoder()
    df["commodity_encoded"] = le.fit_transform(df["commodity"])

    df_clean = df.dropna(subset=FEATURE_COLS + [TARGET_COL]).reset_index(drop=True)
    print(f"  Clean rows     : {len(df_clean):,}")

    X = df_clean[FEATURE_COLS].values
    y = df_clean[TARGET_COL].values

    return X, y, le, df_clean


# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Evaluate helper
# ─────────────────────────────────────────────────────────────────────────────
def evaluate(name: str, model, X_test, y_test) -> dict:
    """Prints and returns MAE, RMSE, R2 for a fitted model."""
    y_pred = model.predict(X_test)
    mae  = mean_absolute_error(y_test, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    ss_res = float(np.sum((y_test - y_pred) ** 2))
    ss_tot = float(np.sum((y_test - y_test.mean()) ** 2))
    r2   = 1 - (ss_res / ss_tot)

    print(f"\n  -- {name} --")
    print(f"     MAE  : Rs {mae:.2f}/kg")
    print(f"     RMSE : Rs {rmse:.2f}/kg")
    print(f"     R2   : {r2:.4f}")
    return {"model": name, "MAE": round(mae, 2), "RMSE": round(rmse, 2), "R2": round(r2, 4)}


# ─────────────────────────────────────────────────────────────────────────────
# Step 3: Main Training Routine
# ─────────────────────────────────────────────────────────────────────────────
def train():
    ensure_data()

    X, y, le, df_clean = load_and_prepare(FEATURE_CSV)

    # Time-aware split — last 20% kept as test (no shuffling to avoid leakage)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    print(f"\n[SPLIT] Train: {len(X_train):,} rows | Test: {len(X_test):,} rows")

    # Scale features (important for Linear Regression)
    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)

    print("\n[TRAIN] Training models...")

    # Model 1: Linear Regression Baseline
    lr = LinearRegression()
    lr.fit(X_train_sc, y_train)
    lr_results = evaluate("Linear Regression (Baseline)", lr, X_test_sc, y_test)

    # Model 2: XGBoost Regressor
    xgb = XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=-1,
        verbosity=0,
    )
    xgb.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    xgb_results = evaluate("XGBoost Regressor (Sprint 2)", xgb, X_test, y_test)

    # Save Artifacts
    print("\n[SAVE] Persisting model artifacts...")
    lr_path      = os.path.join(MODELS_DIR, "linear_regression_baseline.pkl")
    xgb_path     = os.path.join(MODELS_DIR, "xgboost_price_model.pkl")
    scaler_path  = os.path.join(MODELS_DIR, "preprocessor.pkl")
    encoder_path = os.path.join(MODELS_DIR, "label_encoder.pkl")
    eval_path    = os.path.join(MODELS_DIR, "evaluation_report.json")

    joblib.dump(lr,     lr_path)
    joblib.dump(xgb,    xgb_path)
    joblib.dump(scaler, scaler_path)
    joblib.dump(le,     encoder_path)

    report = {
        "sprint": "Sprint 2 - Baseline Price Recommendation",
        "feature_columns": FEATURE_COLS,
        "target": TARGET_COL,
        "train_rows": len(X_train),
        "test_rows":  len(X_test),
        "commodities": sorted(df_clean["commodity"].unique().tolist()),
        "results": [lr_results, xgb_results],
        "best_model": "XGBoost" if xgb_results["RMSE"] < lr_results["RMSE"] else "LinearRegression",
    }
    with open(eval_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n  OK  linear_regression_baseline.pkl  -> {lr_path}")
    print(f"  OK  xgboost_price_model.pkl         -> {xgb_path}")
    print(f"  OK  preprocessor.pkl                -> {scaler_path}")
    print(f"  OK  label_encoder.pkl               -> {encoder_path}")
    print(f"  OK  evaluation_report.json          -> {eval_path}")

    # Summary Table
    print("\n" + "=" * 60)
    print("  SPRINT 2 - MODEL EVALUATION SUMMARY")
    print("=" * 60)
    print(f"  {'Model':<35} {'MAE':>10} {'RMSE':>10} {'R2':>8}")
    print(f"  {'-'*35} {'-'*10} {'-'*10} {'-'*8}")
    for r in [lr_results, xgb_results]:
        print(f"  {r['model']:<35} Rs{r['MAE']:>7.2f} Rs{r['RMSE']:>7.2f} {r['R2']:>8.4f}")
    print("=" * 60)
    print(f"  Best model -> {report['best_model']}")
    print("=" * 60 + "\n")

    return xgb_path, scaler_path, encoder_path


# ─────────────────────────────────────────────────────────────────────────────
# Step 4: Inference Helper  (used by FastAPI /api/predict-price endpoint)
# ─────────────────────────────────────────────────────────────────────────────
def load_model(models_dir: str = MODELS_DIR):
    """Loads the saved XGBoost model + label encoder for inference."""
    xgb = joblib.load(os.path.join(models_dir, "xgboost_price_model.pkl"))
    le  = joblib.load(os.path.join(models_dir, "label_encoder.pkl"))
    return xgb, le


def predict_price(
    commodity: str,
    lag_1: float,
    lag_7: float,
    lag_14: float,
    lag_30: float,
    rolling_mean_7: float,
    rolling_mean_30: float,
    rolling_std_7: float,
    rolling_std_30: float,
    pct_change_7: float,
    pct_change_30: float,
    models_dir: str = MODELS_DIR,
    confidence_rmse: float = 15.0,
) -> dict:
    """
    FastAPI-ready inference function.
    Returns recommended price, lower/upper band, and trend direction.
    """
    xgb, le = load_model(models_dir)

    try:
        commodity_enc = le.transform([commodity])[0]
    except ValueError:
        commodity_enc = int(np.mean(le.transform(le.classes_)))

    features = np.array([[
        commodity_enc,
        lag_1, lag_7, lag_14, lag_30,
        rolling_mean_7, rolling_mean_30,
        rolling_std_7, rolling_std_30,
        pct_change_7, pct_change_30,
    ]])

    pred  = float(xgb.predict(features)[0])
    lower = round(pred - (1.96 * confidence_rmse), 2)
    upper = round(pred + (1.96 * confidence_rmse), 2)
    pred  = round(pred, 2)

    if pred > rolling_mean_7 * 1.01:
        trend = "UPWARD"
    elif pred < rolling_mean_7 * 0.99:
        trend = "DOWNWARD"
    else:
        trend = "STABLE"

    return {
        "recommended_price": pred,
        "price_band":  {"lower": max(lower, 0.0), "upper": upper},
        "trend":       trend,
        "unit":        "INR/kg",
        "commodity":   commodity,
        "disclaimer": (
            "This is an AI-estimated reference price based on historical market data. "
            "It is not a guaranteed transaction price. Actual scrap prices depend on "
            "grade, condition, local demand, and negotiation."
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    train()
