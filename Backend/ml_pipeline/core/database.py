"""Standalone ML database connection and session management."""

from __future__ import annotations

from time import perf_counter

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from .logger import logger
from ..utils import ML_DATABASE_URL

if not ML_DATABASE_URL:
    raise RuntimeError("ML_DATABASE_URL is required for the standalone ML service")

logger.info("Creating ML database engine")
engine = create_engine(
    ML_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args={"connect_timeout": 15},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
logger.info("ML database engine created")


def init_database() -> None:
    started = perf_counter()
    logger.info("Database startup: importing ML database models")
    from . import db_models  # noqa: F401
    logger.info("Database startup: creating or validating tables")
    Base.metadata.create_all(bind=engine)
    logger.info("Database startup: cleaning duplicate source rows")
    with engine.begin() as connection:
        connection.execute(text("""
            DELETE FROM ml_source_observations AS duplicate
            USING ml_source_observations AS kept
            WHERE duplicate.id > kept.id
              AND duplicate.source = kept.source
              AND duplicate.observation_date = kept.observation_date
              AND COALESCE(duplicate.material, '') = COALESCE(kept.material, '')
              AND COALESCE(duplicate.scrap_type, '') = COALESCE(kept.scrap_type, '')
              AND COALESCE(duplicate.commodity, '') = COALESCE(kept.commodity, '')
              AND COALESCE(duplicate.ticker, '') = COALESCE(kept.ticker, '')
              AND COALESCE(duplicate.source_hash, '') = COALESCE(kept.source_hash, '')
        """))
        connection.execute(text("""
            DELETE FROM ml_feature_observations AS duplicate
            USING ml_feature_observations AS kept
            WHERE duplicate.id > kept.id
              AND duplicate.target_source = kept.target_source
              AND duplicate.observation_date = kept.observation_date
              AND COALESCE(duplicate.material, '') = COALESCE(kept.material, '')
              AND COALESCE(duplicate.scrap_type, '') = COALESCE(kept.scrap_type, '')
              AND duplicate.feature_version = kept.feature_version
        """))
        connection.execute(text("""
            UPDATE ml_source_observations
            SET material = COALESCE(material, ''),
                scrap_type = COALESCE(scrap_type, ''),
                commodity = COALESCE(commodity, ''),
                ticker = COALESCE(ticker, ''),
                source_hash = COALESCE(source_hash, '')
            WHERE material IS NULL
               OR scrap_type IS NULL
               OR commodity IS NULL
               OR ticker IS NULL
               OR source_hash IS NULL
        """))
        connection.execute(text("""
            UPDATE ml_feature_observations
            SET material = COALESCE(material, ''),
                scrap_type = COALESCE(scrap_type, '')
            WHERE material IS NULL OR scrap_type IS NULL
        """))
    logger.info("Database startup complete in %.2f seconds", perf_counter() - started)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
