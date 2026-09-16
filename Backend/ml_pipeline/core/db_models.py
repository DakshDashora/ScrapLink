"""Database models owned exclusively by the standalone ML pipeline."""

from sqlalchemy import Column, Date, DateTime, Float, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from .database import Base


class SourceObservation(Base):
    __tablename__ = "ml_source_observations"
    __table_args__ = (
        UniqueConstraint(
            "source", "observation_date", "material", "scrap_type",
            "commodity", "ticker", "source_hash", name="uq_ml_source_observation"
        ),
    )

    id = Column(Integer, primary_key=True)
    source = Column(String(64), nullable=False, index=True)
    observation_date = Column(Date, nullable=False, index=True)
    material = Column(String(128), nullable=True, index=True)
    scrap_type = Column(String(256), nullable=True)
    commodity = Column(String(128), nullable=True)
    ticker = Column(String(64), nullable=True)
    price_inr_per_kg = Column(Float, nullable=True)
    reference_price = Column(Float, nullable=True)
    source_currency = Column(String(16), nullable=True)
    source_unit = Column(String(32), nullable=True)
    traded_contract_lots = Column(Float, nullable=True)
    total_value_lakhs = Column(Float, nullable=True)
    avg_daily_turnover_lakhs = Column(Float, nullable=True)
    premium_value_lakhs = Column(Float, nullable=True)
    source_file = Column(Text, nullable=False)
    source_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class FeatureObservation(Base):
    __tablename__ = "ml_feature_observations"
    __table_args__ = (
        UniqueConstraint(
            "target_source", "observation_date", "material", "scrap_type",
            "feature_version", name="uq_ml_feature_observation"
        ),
    )

    id = Column(Integer, primary_key=True)
    target_source = Column(String(64), nullable=False, index=True)
    observation_date = Column(Date, nullable=False, index=True)
    material = Column(String(128), nullable=False)
    scrap_type = Column(String(256), nullable=True)
    target_price_inr_per_kg = Column(Float, nullable=True)
    feature_version = Column(String(32), nullable=False)
    features = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PipelineRun(Base):
    __tablename__ = "ml_pipeline_runs"

    id = Column(Integer, primary_key=True)
    job_type = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, index=True)
    rows_read = Column(Integer, nullable=True)
    rows_written = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
