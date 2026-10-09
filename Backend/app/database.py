import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
import uuid

# ============================================
# DATABASE URL RESOLUTION
# ============================================
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    from app.config import settings
    DATABASE_URL = settings.DATABASE_URL

# ✅ Ensure psycopg2 driver is used
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
# If it already starts with "postgresql+psycopg2://", leave it alone

print(f"🔗 Using DB driver: {'psycopg2' if 'psycopg2' in DATABASE_URL else 'default'}")

# ============================================
# CREATE ENGINE
# ============================================
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    """Initialize database with pgvector extension"""
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        print("✅ pgvector extension enabled")
    except Exception as e:
        print(f"⚠️ pgvector init error: {e}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()