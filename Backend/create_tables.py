#!/usr/bin/env python3
"""
Create all database tables for ScrapLink
Run: python create_tables.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, init_db, Base
from app.models import (User, Organization, OrganizationMember, OTPRecord,
                       ScrapCategory, ScrapListing, ListingMedia)

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
    
    print("\n🚀 Next steps:")
    print("   1. Run: python seed_categories.py")
    print("   2. Run: uvicorn app.main:app --reload")

if __name__ == "__main__":
    create_tables()