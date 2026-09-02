#!/usr/bin/env python3
"""
Create all database tables for ScrapLink
Run: python create_tables.py
"""

import sys
import os

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, init_db
from app.models import User, Organization, OrganizationMember, OTPRecord
from app.database import Base

def create_tables():
    """Create all tables defined in models"""
    print("📊 Creating database tables...")
    
    # Initialize pgvector extension
    init_db()
    print("✅ pgvector extension enabled")
    
    # Create all tables
    print("📋 Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")
    
    # List created tables
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("\n📋 Tables created:")
    for table in tables:
        print(f"   - {table}")

if __name__ == "__main__":
    create_tables()