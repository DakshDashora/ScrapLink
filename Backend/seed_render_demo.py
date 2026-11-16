import os
import uuid
import random
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import your models and security
from app.models import (
    User, Organization, OrganizationMember, ScrapCategory, 
    ScrapListing, BuyerRequirement, MatchEvent, OTPRecord
)
from app.models.user import UserRole
from app.models.organization import BusinessType, VerificationStatus
from app.models.organization_member import MemberRole
from app.models.scrap_listing import ListingStatus, ListingUnit
from app.models.buyer_requirement import RequirementStatus, RequirementUnit
from app.security import get_password_hash

# ⚠️ PASTE YOUR NEON DATABASE URL HERE ⚠️
NEON_DB_URL = "postgresql://neondb_owner:npg_adsGt2cpf7mY@ep-crimson-salad-a15913c9-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

engine = create_engine(NEON_DB_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def clear_database():
    print("🗑️ Clearing old data...")
    db.query(OTPRecord).delete()
    db.query(MatchEvent).delete()
    db.query(BuyerRequirement).delete()
    db.query(ScrapListing).delete()
    db.query(OrganizationMember).delete()
    db.query(Organization).delete()
    db.query(User).delete()
    db.commit()
    print("✅ Database cleared.")

def create_users_and_orgs():
    print("🏢 Creating 10 Users and Organizations...")
    password = get_password_hash("Password123")
    
    orgs_data = [
        {"name": "Mumbai Metal Traders", "type": BusinessType.PROPRIETORSHIP, "city": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lng": 72.8777, "role": UserRole.SELLER},
        {"name": "Delhi Scrap Recycling", "type": BusinessType.COMPANY, "city": "Delhi", "state": "Delhi", "lat": 28.7041, "lng": 77.1025, "role": UserRole.SELLER},
        {"name": "Bangalore E-Waste Co", "type": BusinessType.PARTNERSHIP, "city": "Bangalore", "state": "Karnataka", "lat": 12.9716, "lng": 77.5946, "role": UserRole.SELLER},
        {"name": "Chennai Plastic Recyclers", "type": BusinessType.COMPANY, "city": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lng": 80.2707, "role": UserRole.SELLER},
        {"name": "Pune Iron & Steel", "type": BusinessType.PROPRIETORSHIP, "city": "Pune", "state": "Maharashtra", "lat": 18.5204, "lng": 73.8567, "role": UserRole.SELLER},
        {"name": "Ahmedabad Copper Works", "type": BusinessType.COMPANY, "city": "Ahmedabad", "state": "Gujarat", "lat": 23.0225, "lng": 72.5714, "role": UserRole.BUYER},
        {"name": "Kolkata Aluminum Corp", "type": BusinessType.COMPANY, "city": "Kolkata", "state": "West Bengal", "lat": 22.5726, "lng": 88.3639, "role": UserRole.BUYER},
        {"name": "Hyderabad Alloys", "type": BusinessType.PARTNERSHIP, "city": "Hyderabad", "state": "Telangana", "lat": 17.3850, "lng": 78.4867, "role": UserRole.BUYER},
        {"name": "Jaipur Brass Traders", "type": BusinessType.PROPRIETORSHIP, "city": "Jaipur", "state": "Rajasthan", "lat": 26.9124, "lng": 75.7873, "role": UserRole.BUYER},
        {"name": "Surat Textile Waste", "type": BusinessType.PARTNERSHIP, "city": "Surat", "state": "Gujarat", "lat": 21.1702, "lng": 72.8311, "role": UserRole.BUYER},
    ]
    
    users = []
    for i, data in enumerate(orgs_data):
        user = User(
            id=uuid.uuid4(),
            full_name=f"Manager {data['name']}",
            email=f"user{i+1}@scraplink.com",
            phone=f"+9198765432{i:02d}",
            password_hash=password,
            role=data["role"],
            email_verified=True,
            phone_verified=True
        )
        db.add(user)
        
        org = Organization(
            id=uuid.uuid4(),
            name=data["name"],
            business_type=data["type"],
            industry_type="Scrap & Recycling",
            location={"city": data["city"], "state": data["state"], "latitude": data["lat"], "longitude": data["lng"]},
            owner_user_id=user.id,
            verification_status=VerificationStatus.VERIFIED
        )
        db.add(org)
        db.flush()
        
        member = OrganizationMember(
            id=uuid.uuid4(),
            organization_id=org.id,
            user_id=user.id,
            role=MemberRole.OWNER
        )
        db.add(member)
        users.append((user, org, data["role"]))
        
    db.commit()
    print("✅ Users and Organizations created.")
    return users

def create_listings_and_requirements(users):
    print("📦 Creating Listings and Requirements based on ML CSV data...")
    categories = {c.name: c.id for c in db.query(ScrapCategory).all()}
    sellers = [u for u in users if u[2] == UserRole.SELLER]
    buyers = [u for u in users if u[2] == UserRole.BUYER]
    
    # ✅ Using exact "material" names and assigning a "scrap_type" as the description
    listings_data = [
        {"mat": "#1 Busheling", "cat": "Steel", "scrap": "Grade 1 Old Steel (#1 5 ft)", "qty": 500, "price": 720},
        {"mat": "6061 Extrusions", "cat": "Aluminium", "scrap": "6061 Extrusions", "qty": 300, "price": 680},
        {"mat": "6063 Extrusions", "cat": "Aluminium", "scrap": "6063 Extrusions", "qty": 1200, "price": 180},
        {"mat": "Al/Cu Radiators", "cat": "Copper", "scrap": "Al/Cu Radiators", "qty": 2000, "price": 130},
        {"mat": "Alternator", "cat": "Electronic Waste", "scrap": "Alternator", "qty": 5000, "price": 38},
        {"mat": "Aluminium", "cat": "Aluminium", "scrap": "Mixed Aluminum Turnings", "qty": 800, "price": 140},
        {"mat": "Brass", "cat": "Brass", "scrap": "Yellow Brass", "qty": 300, "price": 250},
        {"mat": "Chrome Wheels", "cat": "Aluminium", "scrap": "Chrome Wheels", "qty": 800, "price": 420},
        {"mat": "Copper", "cat": "Copper", "scrap": "#1 Copper Bare Bright", "qty": 1000, "price": 45},
        {"mat": "Grade OA Structural Plate", "cat": "Steel", "scrap": "Grade OA Structural Plate", "qty": 1500, "price": 55},
        {"mat": "Heater Cores", "cat": "Copper", "scrap": "Heater Cores", "qty": 2500, "price": 85},
        {"mat": "Lead", "cat": "Lead", "scrap": "Lead Solid Lead", "qty": 600, "price": 210},
        {"mat": "MLC Clips", "cat": "Electronic Waste", "scrap": "MLC Clips", "qty": 400, "price": 450},
        {"mat": "Nickel Cathode", "cat": "Mixed Scrap", "scrap": "Nickel Cathode", "qty": 3000, "price": 32},
        {"mat": "Rod Borings", "cat": "Steel", "scrap": "Rod Borings", "qty": 5000, "price": 12}
    ]
    
    for i, l in enumerate(listings_data):
        seller_user, seller_org, _ = sellers[i % len(sellers)]
        
        if l["cat"] not in categories:
            continue
            
        listing = ScrapListing(
            id=uuid.uuid4(),
            seller_org_id=seller_org.id,
            category_id=categories[l["cat"]],
            material_name=l["mat"],
            grade=l["scrap"], # ✅ Storing scrap_type in the grade/description
            quantity=Decimal(str(l["qty"])),
            unit=ListingUnit.KG,
            asking_price=Decimal(str(l["price"])),
            location=seller_org.location,
            availability_status=ListingStatus.ACTIVE,
            description=f"High grade {l['mat']} ({l['scrap']}) available. Ready for inspection and immediate dispatch from {seller_org.location['city']}."
        )
        db.add(listing)

    # ✅ Using exact "material" names and assigning a "scrap_type" to requirements
    reqs_data = [
        {"mat": "Copper", "cat": "Copper", "scrap": "#1 Copper Wire and Tubing", "qty": 400},
        {"mat": "Steel", "cat": "Steel", "scrap": "HMS 80/20", "qty": 3000},
        {"mat": "Aluminium", "cat": "Aluminium", "scrap": "6063 Extrusions", "qty": 1000},
        {"mat": "Brass", "cat": "Brass", "scrap": "Brass Radiator Ends", "qty": 500},
        {"mat": "Xmas Lights", "cat": "Cables & Wires", "scrap": "Xmas Lights", "qty": 2000}
    ]
    
    for i, r in enumerate(reqs_data):
        buyer_user, buyer_org, _ = buyers[i % len(buyers)]
        
        if r["cat"] not in categories:
            continue
            
        req = BuyerRequirement(
            id=uuid.uuid4(),
            buyer_org_id=buyer_org.id,
            category_id=categories[r["cat"]],
            material_name=r["mat"],
            grade=r["scrap"], # ✅ Storing scrap_type in the grade/description
            quantity=Decimal(str(r["qty"])),
            unit=RequirementUnit.KG,
            status=RequirementStatus.OPEN,
            description=f"Looking for {r['mat']} ({r['scrap']})."
        )
        db.add(req)
    
    db.flush()

    print("🤝 Generating Dummy Match Alerts...")
    all_reqs = db.query(BuyerRequirement).all()
    all_listings = db.query(ScrapListing).all()

    for req in all_reqs:
        num_matches = random.randint(2, 3)
        matched_listings = random.sample(all_listings, min(num_matches, len(all_listings)))
        
        for listing in matched_listings:
            match = MatchEvent(
                id=uuid.uuid4(),
                requirement_id=req.id,
                listing_id=listing.id,
                similarity_score=Decimal(str(round(random.uniform(0.65, 0.95), 2))),
                match_quality="EXCELLENT_MATCH" if random.uniform(0.8, 1.0) > 0.8 else "GOOD_MATCH"
            )
            db.add(match)
        
    db.commit()
    print("✅ Listings, Requirements, and Match Alerts created.")

if __name__ == "__main__":
    print("🚀 Starting Demo Data Seeding...")
    clear_database()
    users = create_users_and_orgs()
    create_listings_and_requirements(users)
    print("\n🎉 SUCCESS! Your Neon database is now full of demo data.")
    print("🔑 Password for ALL users: Password123")
    print("📧 Sellers: user1@scraplink.com to user5@scraplink.com")
    print("📧 Buyers:  user6@scraplink.com to user10@scraplink.com")