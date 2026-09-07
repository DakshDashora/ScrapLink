#!/usr/bin/env python3
"""
Seed scrap categories data
Run: python seed_categories.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.scrap_category import ScrapCategory
import uuid


def seed_categories():
    db = SessionLocal()
    
    categories = [
        # Ferrous Metals
        {"name": "Steel", "description": "Carbon steel scrap, structural steel"},
        {"name": "Stainless Steel", "description": "Stainless steel 304, 316 grades"},
        {"name": "Cast Iron", "description": "Cast iron scrap from industrial machinery"},
        
        # Non-Ferrous Metals
        {"name": "Aluminium", "description": "Aluminium scrap, extrusions, sheets"},
        {"name": "Copper", "description": "Copper wire, tubing, busbars"},
        {"name": "Brass", "description": "Brass scrap, fittings, valves"},
        {"name": "Bronze", "description": "Bronze scrap, bearings, bushings"},
        {"name": "Zinc", "description": "Zinc scrap, die-cast parts"},
        {"name": "Lead", "description": "Lead scrap, batteries, sheets"},
        
        # Electronics
        {"name": "Electronic Waste", "description": "PCBs, circuit boards, e-waste"},
        {"name": "Batteries", "description": "Lithium-ion, lead-acid batteries"},
        {"name": "Cables & Wires", "description": "Copper and aluminum cables"},
        
        # Plastics
        {"name": "Plastic - PET", "description": "PET bottles and containers"},
        {"name": "Plastic - HDPE", "description": "HDPE containers, pipes"},
        {"name": "Plastic - PVC", "description": "PVC pipes, fittings"},
        
        # Others
        {"name": "Glass", "description": "Glass waste, bottles, sheets"},
        {"name": "Paper & Cardboard", "description": "Industrial paper waste"},
        {"name": "Rubber", "description": "Rubber scrap, tires, belts"},
        {"name": "Textile Waste", "description": "Industrial textile waste"},
        {"name": "Mixed Scrap", "description": "Mixed industrial scrap"},
    ]
    
    try:
        for cat in categories:
            existing = db.query(ScrapCategory).filter(
                ScrapCategory.name == cat["name"]
            ).first()
            if not existing:
                category = ScrapCategory(
                    id=uuid.uuid4(),
                    name=cat["name"],
                    description=cat["description"]
                )
                db.add(category)
                print(f"✅ Added category: {cat['name']}")
            else:
                print(f"⏭️ Category already exists: {cat['name']}")
        
        db.commit()
        print(f"\n✅ Seed completed! {len(categories)} categories processed.")
    
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    
    finally:
        db.close()


if __name__ == "__main__":
    seed_categories()