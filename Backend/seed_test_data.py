#!/usr/bin/env python3
"""
Create test data with organizations
Run: python seed_test_data.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.organization import Organization, BusinessType, VerificationStatus
from app.models.organization_member import OrganizationMember, MemberRole
from app.models.scrap_category import ScrapCategory
from app.security import get_password_hash
import uuid


def create_test_data():
    db = SessionLocal()
    
    try:
        # Check if categories exist
        categories = db.query(ScrapCategory).count()
        if categories == 0:
            print("⚠️ No categories found! Please run: python seed_categories.py")
            return
        
        print(f"✅ Found {categories} categories")
        
        # Create a test seller
        seller = db.query(User).filter(User.email == "seller@example.com").first()
        if not seller:
            seller = User(
                id=uuid.uuid4(),
                full_name="Test Seller",
                email="seller@example.com",
                phone="+919876543210",
                password_hash=get_password_hash("SecurePass123"),
                role=UserRole.SELLER,
                email_verified=True,
                phone_verified=True
            )
            db.add(seller)
            db.flush()
            print("✅ Created seller user")
        else:
            print("⏭️ Seller already exists")
        
        # Create organization for seller
        org = db.query(Organization).filter(Organization.name == "Test Steel Industries").first()
        if not org:
            org = Organization(
                id=uuid.uuid4(),
                name="Test Steel Industries",
                business_type=BusinessType.COMPANY,
                industry_type="Steel Manufacturing",
                description="Test company for ScrapLink",
                location={"address": "123 Industrial Area, Mumbai", "city": "Mumbai", "state": "Maharashtra"},
                gstin="27AABCT1234D1ZP",
                owner_user_id=seller.id,
                verification_status=VerificationStatus.VERIFIED
            )
            db.add(org)
            db.flush()
            print("✅ Created organization: Test Steel Industries")
        else:
            print("⏭️ Organization already exists")
        
        # Add seller as owner
        member = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == org.id,
            OrganizationMember.user_id == seller.id
        ).first()
        if not member:
            member = OrganizationMember(
                id=uuid.uuid4(),
                organization_id=org.id,
                user_id=seller.id,
                role=MemberRole.OWNER
            )
            db.add(member)
            print("✅ Added seller as owner")
        
        # Create a test buyer
        buyer = db.query(User).filter(User.email == "buyer@example.com").first()
        if not buyer:
            buyer = User(
                id=uuid.uuid4(),
                full_name="Test Buyer",
                email="buyer@example.com",
                phone="+919876543211",
                password_hash=get_password_hash("SecurePass123"),
                role=UserRole.BUYER,
                email_verified=True,
                phone_verified=True
            )
            db.add(buyer)
            db.flush()
            print("✅ Created buyer user")
        else:
            print("⏭️ Buyer already exists")
        
        # Create organization for buyer
        buyer_org = db.query(Organization).filter(Organization.name == "Test Recycling Co").first()
        if not buyer_org:
            buyer_org = Organization(
                id=uuid.uuid4(),
                name="Test Recycling Co",
                business_type=BusinessType.PARTNERSHIP,
                industry_type="Recycling",
                description="Test recycling company",
                location={"address": "456 Green Zone, Delhi", "city": "Delhi", "state": "Delhi"},
                owner_user_id=buyer.id,
                verification_status=VerificationStatus.VERIFIED
            )
            db.add(buyer_org)
            db.flush()
            print("✅ Created organization: Test Recycling Co")
        else:
            print("⏭️ Buyer organization already exists")
        
        # Add buyer as owner
        member = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == buyer_org.id,
            OrganizationMember.user_id == buyer.id
        ).first()
        if not member:
            member = OrganizationMember(
                id=uuid.uuid4(),
                organization_id=buyer_org.id,
                user_id=buyer.id,
                role=MemberRole.OWNER
            )
            db.add(member)
            print("✅ Added buyer as owner")
        
        db.commit()
        print("\n" + "="*60)
        print("✅ Test data created successfully!")
        print("="*60)
        print("\n📋 Test Users:")
        print(f"   Seller: seller@example.com / SecurePass123")
        print(f"   Buyer:  buyer@example.com / SecurePass123")
        print("\n📋 Organizations:")
        print(f"   Test Steel Industries (Seller)")
        print(f"   Test Recycling Co (Buyer)")
        print("="*60)
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    create_test_data()