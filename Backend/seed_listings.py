#!/usr/bin/env python3
"""
Seed multiple listings with real locations for map/search testing
Run: python seed_listings.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.user import User
from app.models.organization import Organization
from app.models.scrap_listing import ScrapListing, ListingStatus, ListingUnit
from app.models.scrap_category import ScrapCategory
from app.models.organization_member import OrganizationMember
import uuid
from decimal import Decimal


def seed_listings():
    db = SessionLocal()
    
    try:
        # Get seller organization
        seller = db.query(User).filter(User.email == "seller@example.com").first()
        if not seller:
            print("❌ Seller not found. Run: python seed_test_data.py")
            return
        
        org = db.query(Organization).filter(
            Organization.owner_user_id == seller.id
        ).first()
        
        if not org:
            print("❌ Organization not found. Run: python seed_test_data.py")
            return
        
        print(f"✅ Using organization: {org.name}")
        
        # Get categories map
        categories = {c.name: c.id for c in db.query(ScrapCategory).all()}
        
        # Listings data with real Indian city coordinates
        listings_data = [
            # Steel
            {"cat": "Steel", "mat": "MS Steel Scrap", "grade": "Heavy Melting", "qty": 5000, "unit": "kg", "price": 35, "city": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lng": 72.8777},
            {"cat": "Steel", "mat": "MS Turnings", "grade": "Light", "qty": 3000, "unit": "kg", "price": 28, "city": "Delhi", "state": "Delhi", "lat": 28.7041, "lng": 77.1025},
            {"cat": "Steel", "mat": "Steel Plates", "grade": "Industrial", "qty": 8000, "unit": "kg", "price": 42, "city": "Bangalore", "state": "Karnataka", "lat": 12.9716, "lng": 77.5946},
            
            # Stainless Steel
            {"cat": "Stainless Steel", "mat": "SS 304 Scrap", "grade": "304", "qty": 1500, "unit": "kg", "price": 120, "city": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lng": 80.2707},
            {"cat": "Stainless Steel", "mat": "SS 316 Scrap", "grade": "316", "qty": 800, "unit": "kg", "price": 180, "city": "Pune", "state": "Maharashtra", "lat": 18.5204, "lng": 73.8567},
            
            # Aluminium
            {"cat": "Aluminium", "mat": "Aluminium Extrusion", "grade": "6063", "qty": 2000, "unit": "kg", "price": 145, "city": "Ahmedabad", "state": "Gujarat", "lat": 23.0225, "lng": 72.5714},
            {"cat": "Aluminium", "mat": "Aluminium Cans", "grade": "Mixed", "qty": 5000, "unit": "kg", "price": 95, "city": "Kolkata", "state": "West Bengal", "lat": 22.5726, "lng": 88.3639},
            {"cat": "Aluminium", "mat": "Aluminium Sheet", "grade": "Clean", "qty": 3500, "unit": "kg", "price": 130, "city": "Hyderabad", "state": "Telangana", "lat": 17.3850, "lng": 78.4867},
            
            # Copper
            {"cat": "Copper", "mat": "Copper Wire Scrap", "grade": "99.9%", "qty": 500, "unit": "kg", "price": 750, "city": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lng": 72.8777},
            {"cat": "Copper", "mat": "Copper Tubing", "grade": "Clean", "qty": 800, "unit": "kg", "price": 680, "city": "Delhi", "state": "Delhi", "lat": 28.7041, "lng": 77.1025},
            {"cat": "Copper", "mat": "Copper Cable", "grade": "Insulated", "qty": 1200, "unit": "kg", "price": 520, "city": "Bangalore", "state": "Karnataka", "lat": 12.9716, "lng": 77.5946},
            
            # Brass
            {"cat": "Brass", "mat": "Brass Fittings", "grade": "Mixed", "qty": 600, "unit": "kg", "price": 380, "city": "Rajkot", "state": "Gujarat", "lat": 22.3039, "lng": 70.8022},
            {"cat": "Brass", "mat": "Brass Turnings", "grade": "Clean", "qty": 900, "unit": "kg", "price": 350, "city": "Jamnagar", "state": "Gujarat", "lat": 22.4707, "lng": 70.0577},
            
            # Electronic Waste
            {"cat": "Electronic Waste", "mat": "PCB Boards", "grade": "Mixed", "qty": 300, "unit": "kg", "price": 250, "city": "Bangalore", "state": "Karnataka", "lat": 12.9716, "lng": 77.5946},
            {"cat": "Electronic Waste", "mat": "Computer Parts", "grade": "Mixed", "qty": 500, "unit": "kg", "price": 180, "city": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lng": 72.8777},
            
            # Cables & Wires
            {"cat": "Cables & Wires", "mat": "Copper Cables", "grade": "Mixed", "qty": 1500, "unit": "kg", "price": 420, "city": "Pune", "state": "Maharashtra", "lat": 18.5204, "lng": 73.8567},
            {"cat": "Cables & Wires", "mat": "Aluminium Cables", "grade": "Mixed", "qty": 2000, "unit": "kg", "price": 120, "city": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lng": 80.2707},
            
            # Zinc
            {"cat": "Zinc", "mat": "Zinc Die Cast", "grade": "Mixed", "qty": 700, "unit": "kg", "price": 210, "city": "Noida", "state": "Uttar Pradesh", "lat": 28.5355, "lng": 77.3910},
            
            # Batteries
            {"cat": "Batteries", "mat": "Lead Acid Batteries", "grade": "Used", "qty": 3000, "unit": "kg", "price": 85, "city": "Ahmedabad", "state": "Gujarat", "lat": 23.0225, "lng": 72.5714},
            {"cat": "Batteries", "mat": "Lithium Batteries", "grade": "Used", "qty": 500, "unit": "kg", "price": 150, "city": "Bangalore", "state": "Karnataka", "lat": 12.9716, "lng": 77.5946},
            
            # Plastic
            {"cat": "Plastic - PET", "mat": "PET Bottles", "grade": "Clean", "qty": 10000, "unit": "kg", "price": 45, "city": "Delhi", "state": "Delhi", "lat": 28.7041, "lng": 77.1025},
            {"cat": "Plastic - HDPE", "mat": "HDPE Containers", "grade": "Mixed", "qty": 5000, "unit": "kg", "price": 55, "city": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lng": 72.8777},
            
            # Cast Iron
            {"cat": "Cast Iron", "mat": "CI Scrap", "grade": "Heavy", "qty": 6000, "unit": "kg", "price": 32, "city": "Kolkata", "state": "West Bengal", "lat": 22.5726, "lng": 88.3639},
        ]
        
        created = 0
        for data in listings_data:
            cat_id = categories.get(data["cat"])
            if not cat_id:
                print(f"⚠️ Category not found: {data['cat']}")
                continue
            
            listing = ScrapListing(
                id=uuid.uuid4(),
                seller_org_id=org.id,
                category_id=cat_id,
                material_name=data["mat"],
                grade=data["grade"],
                description=f"High quality {data['mat']} available for immediate sale. Located in {data['city']}.",
                quantity=Decimal(str(data["qty"])),
                unit=ListingUnit(data["unit"]),
                asking_price=Decimal(str(data["price"])),
                location={
                    "address": f"Industrial Area, {data['city']}",
                    "city": data["city"],
                    "state": data["state"],
                    "country": "India",
                    "latitude": data["lat"],
                    "longitude": data["lng"]
                },
                availability_status=ListingStatus.ACTIVE
            )
            db.add(listing)
            created += 1
            print(f"✅ Added: {data['mat']} in {data['city']}")
        
        db.commit()
        print(f"\n✅ Successfully created {created} listings!")
        print(f"📍 Locations across India - ready for map testing")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_listings()