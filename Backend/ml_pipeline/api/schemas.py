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
    updated: StrictInt = Field(default=0, ge=0)
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
    analysis_report: dict[str, Any]


class FeatureEngineeringResponse(StrictSchema):
    status: Literal["succeeded"]
    run_id: StrictInt = Field(gt=0)
    persistence: PersistenceSummary
    eligibility: dict[str, Any]


class WeeklyAnalysisResponse(StrictSchema):
    status: Literal["succeeded"]
    manifest: dict[str, Any]
    analysis_report: dict[str, Any]


class TrainingResponse(StrictSchema):
    status: Literal["skipped", "promoted"]
    reason: StrictStr | None = None
    version: StrictStr | None = None
    artifact_files: list[StrictStr] | None = None
    feature_persistence: PersistenceSummary | None = None
    legacy_scrap_rows_converted: StrictInt | None = Field(default=None, ge=0)
    analysis_report: dict[str, Any] | None = None
    metrics: dict[str, Any] | None = None
    collection_dates: StrictInt | None = Field(default=None, ge=0)
    minimum_collection_dates: StrictInt | None = Field(default=None, ge=0)
    eligible_rows: StrictInt | None = Field(default=None, ge=0)
    minimum_training_rows: StrictInt | None = Field(default=None, ge=0)
    validation_mae: StrictFloat | None = Field(default=None, ge=0)
    maximum_validation_mae: StrictFloat | None = Field(default=None, ge=0)
    active_validation_mae: StrictFloat | None = Field(default=None, ge=0)
    promotion: dict[str, Any] | None = None


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


# ==============================================================================
# SPRINT 3: Semantic Matching & Trust/Anomaly Schemas
# ==============================================================================

class EmbeddingRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    text: str | None = None
    material_name: str | None = None
    category: str | None = None
    grade: str | None = None
    description: str | None = None
    quantity: float | None = None
    unit: str | None = None
    location: Any = None


class EmbeddingResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: Literal["success"]
    model_version: str
    embedding: list[float]
    dimension: int
    normalized_text: str


class MatchCandidateListing(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    material_name: str
    category: str | None = None
    grade: str | None = None
    description: str | None = None
    quantity: float
    unit: str = "kg"
    asking_price: float | None = None
    availability_status: str = "Active"
    location: Any = None
    embedding: list[float] | None = None


class MatchRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    requirement_text: str | None = None
    requirement_vector: list[float] | None = None
    material_name: str | None = None
    category: str | None = None
    grade: str | None = None
    description: str | None = None
    quantity: float | None = None
    unit: str | None = None
    location: Any = None
    candidate_listings: list[MatchCandidateListing]
    top_k: int = 10
    min_similarity: float = 0.30
    enforce_active_only: bool = True


class RankedMatchItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    listing_id: str
    material_name: str
    category: str | None = None
    grade: str | None = None
    quantity: float
    unit: str
    asking_price: float | None = None
    location: Any = None
    similarity_score: float
    match_quality: str
    hard_constraints_passed: bool


class MatchResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: Literal["success"]
    total_candidates_evaluated: int
    matches_found: int
    top_matches: list[RankedMatchItem]
    model_version: str
    disclaimer: str


class TrustScoreRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    material_name: str
    asking_price: float | None = None
    quantity: float
    unit: str = "kg"
    category: str | None = None
    grade: str | None = None
    description: str | None = None
    location: Any = None
    benchmark_price: float | None = None


class TrustScoreResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: Literal["success"]
    indicator: str
    is_unusual_pattern: bool
    anomaly_score: float
    confidence_level: str
    flags: list[str]
    buyer_guidance: str
    features_evaluated: dict[str, float]
    model_version: str
    estimate_type: str
    is_fraud_probability: bool
    disclaimer: str
