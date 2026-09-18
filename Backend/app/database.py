import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
import uuid

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    from app.config import settings
    DATABASE_URL = settings.DATABASE_URL

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()



def init_db():
    """Initialize database with pgvector extension"""
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        print(" pgvector extension enabled")
    except Exception as e:
        print(f" pgvector init error: {e}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()