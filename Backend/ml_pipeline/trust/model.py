"""Baseline Isolation Forest model trainer and persistence module.

Trains and versions a baseline Isolation Forest model using marketplace listing features.
Adheres to Sprint 3 specifications: decision-support anomaly detection without
claiming fraud probabilities.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

from .feature_extractor import FEATURE_NAMES, extract_listing_features, to_feature_vector

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_FILENAME = "isolation_forest_v1.joblib"
METADATA_FILENAME = "metadata.json"
MODEL_VERSION = "isoforest-v1.0.0-20261021"


def get_default_seed_records() -> list[dict[str, Any]]:
    """Representative marketplace listing dataset for training the baseline model."""
    records = [
        # Normal listings across various scrap metals and quantities
        {"material_name": "MS Steel Scrap", "category": "Steel", "grade": "Heavy Melting", "asking_price": 35, "quantity": 5000, "unit": "kg", "description": "Clean heavy melting steel scrap", "location": {"city": "Mumbai", "state": "Maharashtra", "lat": 19.07, "lng": 72.87}},
        {"material_name": "MS Turnings", "category": "Steel", "grade": "Light", "asking_price": 28, "quantity": 3000, "unit": "kg", "description": "Dry industrial turnings", "location": {"city": "Delhi", "state": "Delhi", "lat": 28.7, "lng": 77.1}},
        {"material_name": "Steel Plates", "category": "Steel", "grade": "Industrial", "asking_price": 42, "quantity": 8000, "unit": "kg", "description": "Assorted cut plates", "location": {"city": "Bangalore", "state": "Karnataka", "lat": 12.97, "lng": 77.59}},
        {"material_name": "SS 304 Scrap", "category": "Stainless Steel", "grade": "304", "asking_price": 120, "quantity": 1500, "unit": "kg", "description": "Tested 304 stainless steel pipes and sheet cuttings", "location": {"city": "Chennai", "state": "Tamil Nadu", "lat": 13.08, "lng": 80.27}},
        {"material_name": "SS 316 Scrap", "category": "Stainless Steel", "grade": "316", "asking_price": 180, "quantity": 800, "unit": "kg", "description": "Non-magnetic SS 316 valves and scrap", "location": {"city": "Pune", "state": "Maharashtra", "lat": 18.52, "lng": 73.85}},
        {"material_name": "Aluminium Extrusion", "category": "Aluminium", "grade": "6063", "asking_price": 145, "quantity": 2000, "unit": "kg", "description": "Clean architectural 6063 extrusions", "location": {"city": "Ahmedabad", "state": "Gujarat", "lat": 23.02, "lng": 72.57}},
        {"material_name": "Aluminium Cans", "category": "Aluminium", "grade": "Mixed", "asking_price": 95, "quantity": 5000, "unit": "kg", "description": "Baled UBC cans ready for loading", "location": {"city": "Kolkata", "state": "West Bengal", "lat": 22.57, "lng": 88.36}},
        {"material_name": "Aluminium Sheet", "category": "Aluminium", "grade": "Clean", "asking_price": 130, "quantity": 3500, "unit": "kg", "description": "Industrial clean sheet scrap", "location": {"city": "Hyderabad", "state": "Telangana", "lat": 17.38, "lng": 78.48}},
        {"material_name": "Copper Wire Scrap", "category": "Copper", "grade": "#1 Bare Bright", "asking_price": 760, "quantity": 1000, "unit": "kg", "description": "Bright clean stripped copper wire", "location": {"city": "Mumbai", "state": "Maharashtra", "lat": 19.07, "lng": 72.87}},
        {"material_name": "Copper Tubes", "category": "Copper", "grade": "#2 Copper", "asking_price": 710, "quantity": 1200, "unit": "kg", "description": "Clean plumbing tubes", "location": {"city": "Jaipur", "state": "Rajasthan", "lat": 26.91, "lng": 75.78}},
        {"material_name": "Honey Brass Scrap", "category": "Brass", "grade": "Honey", "asking_price": 480, "quantity": 1500, "unit": "kg", "description": "Sanitary and industrial brass fittings", "location": {"city": "Jamnagar", "state": "Gujarat", "lat": 22.47, "lng": 70.06}},
        {"material_name": "Zinc Dross", "category": "Zinc", "grade": "Die Cast", "asking_price": 240, "quantity": 2500, "unit": "kg", "description": "Galvanizing zinc dross", "location": {"city": "Kanpur", "state": "Uttar Pradesh", "lat": 26.44, "lng": 80.33}},
        {"material_name": "Lead Battery Scrap", "category": "Lead", "grade": "Rains", "asking_price": 180, "quantity": 4000, "unit": "kg", "description": "Drained whole intact battery scrap", "location": {"city": "Delhi", "state": "Delhi", "lat": 28.7, "lng": 77.1}},
        
        # Variations with small price/qty noise to establish natural distribution
        {"material_name": "MS Steel Scrap", "category": "Steel", "grade": "Heavy Melting", "asking_price": 37, "quantity": 12000, "unit": "kg", "description": "Factory demolition scrap", "location": {"city": "Nagpur", "state": "Maharashtra", "lat": 21.14, "lng": 79.08}},
        {"material_name": "Aluminium Extrusion", "category": "Aluminium", "grade": "6063", "asking_price": 142, "quantity": 600, "unit": "kg", "description": "Window profile cuttings", "location": {"city": "Surat", "state": "Gujarat", "lat": 21.17, "lng": 72.83}},
        {"material_name": "Copper Wire Scrap", "category": "Copper", "grade": "#1 Bare Bright", "asking_price": 780, "quantity": 500, "unit": "kg", "description": "High purity electric copper wire", "location": {"city": "Coimbatore", "state": "Tamil Nadu", "lat": 11.01, "lng": 76.95}},
        {"material_name": "Honey Brass Scrap", "category": "Brass", "grade": "Honey", "asking_price": 465, "quantity": 2200, "unit": "kg", "description": "Heavy brass turnings and valves", "location": {"city": "Rajkot", "state": "Gujarat", "lat": 22.30, "lng": 70.80}},
        
        # Distinct anomalous patterns (for testing detection)
        # Extreme low price (10 INR/kg for Copper - 98% discount)
        {"material_name": "Copper Wire Scrap", "category": "Copper", "grade": "#1", "asking_price": 10, "quantity": 50000, "unit": "kg", "description": "Super cheap copper wire immediate cash only", "location": None},
        # Extreme high price (500 INR/kg for MS Steel - 14x benchmark)
        {"material_name": "MS Steel Scrap", "category": "Steel", "grade": "Light", "asking_price": 500, "quantity": 100, "unit": "kg", "description": "", "location": None},
    ]
    return records


def train_baseline_isolation_forest(
    records: list[dict[str, Any]] | None = None,
    contamination: float = 0.10,
    random_state: int = 42,
) -> dict[str, Any]:
    """Train the baseline Isolation Forest model and persist artifacts to disk."""
    if not records or len(records) < 5:
        records = get_default_seed_records()

    vectors: list[list[float]] = []
    for rec in records:
        feats = extract_listing_features(
            material_name=rec.get("material_name", ""),
            asking_price=rec.get("asking_price"),
            quantity=rec.get("quantity", 100),
            unit=rec.get("unit", "kg"),
            category=rec.get("category"),
            grade=rec.get("grade"),
            description=rec.get("description"),
            location=rec.get("location"),
        )
        vectors.append(to_feature_vector(feats))

    X = np.array(vectors, dtype=np.float64)

    # Train Isolation Forest
    model = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(X)

    # Persist artifact
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = ARTIFACTS_DIR / MODEL_FILENAME
    joblib.dump(model, model_path)

    metadata = {
        "model_version": MODEL_VERSION,
        "algorithm": "IsolationForest",
        "contamination": contamination,
        "n_estimators": 100,
        "feature_names": FEATURE_NAMES,
        "trained_records_count": len(records),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "active",
        "purpose": "Decision-support listing anomaly detection",
    }
    
    meta_path = ARTIFACTS_DIR / METADATA_FILENAME
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return {
        "status": "success",
        "model_version": MODEL_VERSION,
        "trained_records": len(records),
        "model_path": str(model_path),
        "metadata_path": str(meta_path),
    }


def load_baseline_isolation_forest() -> tuple[IsolationForest, dict[str, Any]]:
    """Load the persisted Isolation Forest model and its metadata."""
    model_path = ARTIFACTS_DIR / MODEL_FILENAME
    meta_path = ARTIFACTS_DIR / METADATA_FILENAME

    if not model_path.exists() or not meta_path.exists():
        # Train baseline if not yet present
        train_baseline_isolation_forest()

    model = joblib.load(model_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    return model, metadata
