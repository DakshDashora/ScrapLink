"""Standalone ML database connection and session management."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from ..utils import ML_DATABASE_URL

if not ML_DATABASE_URL:
    raise RuntimeError("ML_DATABASE_URL is required for the standalone ML service")

engine = create_engine(
    ML_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args={"connect_timeout": 15},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def init_database() -> None:
    from . import db_models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
