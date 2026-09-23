"""Strict Pydantic contracts for the standalone ML service."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt, StrictStr


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class JobTriggerRequest(StrictSchema):
    request_id: StrictStr | None = Field(
        default=None,
        description="Optional caller-supplied identifier for tracing a scheduled request.",
    )


class PredictionRequest(StrictSchema):
    commodity: StrictStr = Field(min_length=1, max_length=128)
    lag_1: StrictFloat | None = Field(default=None, ge=0)
    lag_7: StrictFloat | None = Field(default=None, ge=0)
    lag_14: StrictFloat | None = Field(default=None, ge=0)
    lag_30: StrictFloat | None = Field(default=None, ge=0)
    rolling_mean_7: StrictFloat | None = Field(default=None, ge=0)
    rolling_mean_30: StrictFloat | None = Field(default=None, ge=0)
    rolling_std_7: StrictFloat | None = Field(default=None, ge=0)
    rolling_std_30: StrictFloat | None = Field(default=None, ge=0)
    pct_change_7: StrictFloat | None = None
    pct_change_30: StrictFloat | None = None


class PersistenceSummary(StrictSchema):
    attempted: StrictInt = Field(ge=0)
    inserted: StrictInt = Field(ge=0)
    skipped: StrictInt = Field(ge=0)


class HealthResponse(StrictSchema):
    status: Literal["ok"]
    service: Literal["ml_pipeline"]


class PredictionResponse(StrictSchema):
    status: Literal["success"]
    commodity: StrictStr
    estimated_price_p10_inr_per_kg: StrictFloat = Field(ge=0)
    estimated_price_p50_inr_per_kg: StrictFloat = Field(ge=0)
    estimated_price_p90_inr_per_kg: StrictFloat = Field(ge=0)
    model_version: StrictStr
    prediction_date: StrictStr | None = None
    estimate_type: Literal["scrap_market_reference"]
    is_guaranteed_transaction_price: bool
    recommended_price: StrictFloat = Field(ge=0)
    price_band: dict[str, StrictFloat]
    trend: Literal["UPWARD", "DOWNWARD", "STABLE"]
    unit: Literal["INR/kg"]
    disclaimer: StrictStr


class DailyIngestionResponse(StrictSchema):
    status: Literal["succeeded"]
    run_id: StrictInt = Field(gt=0)
    persistence: PersistenceSummary
    details: dict[str, Any]


class FeatureEngineeringResponse(StrictSchema):
    status: Literal["succeeded"]
    run_id: StrictInt = Field(gt=0)
    persistence: PersistenceSummary
    eligibility: dict[str, Any]


class WeeklyAnalysisResponse(StrictSchema):
    status: Literal["succeeded"]
    manifest: dict[str, Any]


class TrainingResponse(StrictSchema):
    status: Literal["skipped", "promoted"]
    reason: StrictStr | None = None
    version: StrictStr | None = None
    metrics: dict[str, Any] | None = None
    collection_dates: StrictInt | None = Field(default=None, ge=0)
    minimum_collection_dates: StrictInt | None = Field(default=None, ge=0)
    eligible_rows: StrictInt | None = Field(default=None, ge=0)
    minimum_training_rows: StrictInt | None = Field(default=None, ge=0)


class JobStatusResponse(StrictSchema):
    run_id: StrictInt = Field(gt=0)
    job_type: StrictStr
    status: StrictStr
    rows_read: StrictInt | None = Field(default=None, ge=0)
    rows_written: StrictInt | None = Field(default=None, ge=0)
    details: dict[str, Any] | None = None
    error_message: StrictStr | None = None
    started_at: StrictStr
    completed_at: StrictStr | None = None
