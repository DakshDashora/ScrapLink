"""Compatibility entry point for the canonical feature pipeline."""

from .trainable import build_trainable_dataset
from .reference_features import build_reference_price_dataset


def engineer_features(processed_csv_path=None, output_dir=None):
    """Generate the leakage-safe trainable dataset and return its path."""
    return build_trainable_dataset()["path"]


def engineer_reference_features():
    """Build the separate Yahoo public-market reference dataset."""
    return build_reference_price_dataset()["path"]
