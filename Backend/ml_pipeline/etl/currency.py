"""Strict conversion of supported source prices into INR per kilogram."""

from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache
import math

import requests

LB_PER_KG = 2.2046226218487757
FRANKFURTER_API = "https://api.frankfurter.dev/v1"


@lru_cache(maxsize=512)
def usd_to_inr_rate(observation_date: date) -> tuple[float, date]:
    """Return the published USD-to-INR rate on or before an observation date."""
    response = requests.get(
        f"{FRANKFURTER_API}/{observation_date.isoformat()}",
        params={"base": "USD", "symbols": "INR"},
        timeout=(5, 20),
    )
    response.raise_for_status()
    payload = response.json()
    try:
        rate = float(payload["rates"]["INR"])
        effective_date = date.fromisoformat(payload["date"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"FX provider returned an invalid USD/INR rate for {observation_date}"
        ) from exc
    if not math.isfinite(rate) or rate <= 0:
        raise ValueError(f"FX provider returned a non-positive USD/INR rate for {observation_date}")
    if effective_date > observation_date:
        raise ValueError(
            f"FX provider returned a future rate date {effective_date} "
            f"for observation date {observation_date}"
        )
    if observation_date - effective_date > timedelta(days=7):
        raise ValueError(
            f"FX provider rate for {observation_date} is stale "
            f"(latest rate date: {effective_date})"
        )
    return rate, effective_date


def convert_to_inr_per_kg(
    price: float,
    currency: str,
    unit: str,
    observation_date: date,
) -> tuple[float, float, date]:
    """Convert a source price and return INR/kg, FX rate, and rate date."""
    value = float(price)
    if not math.isfinite(value) or value <= 0:
        raise ValueError("Source price must be finite and positive")

    normalized_currency = currency.strip().upper()
    normalized_unit = unit.strip().lower()
    if normalized_currency not in {"INR", "USD"}:
        raise ValueError(f"Unsupported source currency for INR/kg conversion: {currency!r}")
    if normalized_unit not in {"kg", "lb"}:
        raise ValueError(f"Unsupported source weight unit for INR/kg conversion: {unit!r}")

    if normalized_currency == "USD":
        fx_rate, fx_date = usd_to_inr_rate(observation_date)
    else:
        fx_rate, fx_date = 1.0, observation_date

    per_kg = value * fx_rate
    if normalized_unit == "lb":
        per_kg *= LB_PER_KG
    if not math.isfinite(per_kg) or per_kg <= 0:
        raise ValueError("Converted INR/kg price must be finite and positive")
    return per_kg, fx_rate, fx_date
