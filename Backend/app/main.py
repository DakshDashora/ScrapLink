from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, engine, Base, SessionLocal
from app.routers import auth_router, otp_router, org_router, listings_router
from app.routers.categories import router as categories_router
from app.config import settings
from app.utils.cloudinary_service import init_cloudinary
from app.models import (
    User, Organization, OrganizationMember, OTPRecord,
    ScrapCategory, ScrapListing, ListingMedia
)
from app.routers.requirements import router as requirements_router
from app.routers.prediction import router as prediction_router
from app.routers.trust import router as trust_router
from app.routers.matches import router as matches_router
from app.routers.ml_options import router as ml_options_router


import uuid


app = FastAPI(
    title=settings.APP_NAME,
    description="B2B Industrial Scrap Exchange Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(otp_router)
app.include_router(org_router)
app.include_router(listings_router)
app.include_router(categories_router)
app.include_router(prediction_router)
app.include_router(requirements_router)
app.include_router(trust_router)
app.include_router(matches_router)
app.include_router(ml_options_router)





from sqlalchemy import text

def create_vector_indexes():
    """Create HNSW indexes for pgvector if they don't exist"""
    with engine.connect() as conn:
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS listing_embedding_hnsw_idx "
            "ON listing_embeddings USING hnsw (embedding vector_cosine_ops);"
        ))
        # Index for requirements
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS requirement_embedding_hnsw_idx "
            "ON requirement_embeddings USING hnsw (embedding vector_cosine_ops);"
        ))
        conn.commit()
    print(" HNSW vector indexes verified/created")

def seed_categories_if_empty():
    """Seed categories if the table is empty"""
    db = SessionLocal()
    try:
        count = db.query(ScrapCategory).count()
        if count > 0:
            print(f" Categories already seeded ({count} found)")
            return

        print(" Seeding categories...")
        categories = [
            {"name": "Steel", "description": "Carbon steel scrap, structural steel"},
            {"name": "Stainless Steel", "description": "Stainless steel 304, 316 grades"},
            {"name": "Cast Iron", "description": "Cast iron scrap from industrial machinery"},
            {"name": "Aluminium", "description": "Aluminium scrap, extrusions, sheets"},
            {"name": "Copper", "description": "Copper wire, tubing, busbars"},
            {"name": "Brass", "description": "Brass scrap, fittings, valves"},
            {"name": "Bronze", "description": "Bronze scrap, bearings, bushings"},
            {"name": "Zinc", "description": "Zinc scrap, die-cast parts"},
            {"name": "Lead", "description": "Lead scrap, batteries, sheets"},
            {"name": "Electronic Waste", "description": "PCBs, circuit boards, e-waste"},
            {"name": "Batteries", "description": "Lithium-ion, lead-acid batteries"},
            {"name": "Cables & Wires", "description": "Copper and aluminum cables"},
            {"name": "Plastic - PET", "description": "PET bottles and containers"},
            {"name": "Plastic - HDPE", "description": "HDPE containers, pipes"},
            {"name": "Plastic - PVC", "description": "PVC pipes, fittings"},
            {"name": "Glass", "description": "Glass waste, bottles, sheets"},
            {"name": "Paper & Cardboard", "description": "Industrial paper waste"},
            {"name": "Rubber", "description": "Rubber scrap, tires, belts"},
            {"name": "Textile Waste", "description": "Industrial textile waste"},
            {"name": "Mixed Scrap", "description": "Mixed industrial scrap"},
        ]

        for cat in categories:
            db.add(ScrapCategory(
                id=uuid.uuid4(),
                name=cat["name"],
                description=cat["description"]
            ))

        db.commit()
        print(f" Seeded {len(categories)} categories")
    except Exception as e:
        db.rollback()
        print(f" Seeding error: {e}")
    finally:
        db.close()

def seed_ml_options_if_empty():
    """Seed materials and scrap types for frontend dropdowns"""
    from app.models.ml_reference import MLMaterial, MLScrapType
    db = SessionLocal()
    try:
        if db.query(MLMaterial).count() == 0:
            materials = [
                "#1 Busheling", "6061 Extrusions", "6063 Extrusions", "Al/Cu Radiators", 
                "Alternator", "Aluminium", "Brass", "Chrome Wheels", "Copper", 
                "Grade OA Structural Plate", "Heater Cores", "Lead", "MLC Clips", 
                "Nickel Cathode", "Rod Borings", "Romex® Wire", "Scrap Auto Batteries", 
                "Scrap Electric Motors", "Shredded Auto Scrap", "Starters", "Steel", 
                "Tin slab", "UBC", "Xmas Lights", "Zinc"
            ]
            for m in materials:
                if m: db.add(MLMaterial(name=m))
            
        if db.query(MLScrapType).count() == 0:
            scrap_types = [
                "Copper Transformer Scrap", "Brass Radiator Ends", "Xmas Lights", "MLC Clips",
                "HMS 80/20", "70/30 Brass Scrap", "Mixed Aluminum Turnings", "#1 Copper Bare Bright",
                "Copper Tube", "80/20 Brass Scrap", "#1 Copper Wire and Tubing", "E.C. Aluminum Wire",
                "Aluminum ingots", "#2 Copper Wire and Tubing", "Copper Radiators", "Copper utensil scrap",
                "Scrap Electric Motors", "Braziery Copper", "#3 Copper - Light Copper", "Aluminum utensil scrap",
                "6061 Extrusions", "Tin slab", "Al/Cu Radiators", "Copper heavy scrap", "Grade 1 Old Steel (#1 5 ft)",
                "Mixed Brass", "UBC", "Grade OA Structural Plate", "#1 Busheling", "Aluminum Transformers",
                "Lead Scrap", "Aluminum Radiators", "Rod Borings", "Aluminum Cuttings", "Lead Wheel Weights",
                "Cast Iron Scrap", "Scrap Auto Batteries", "Starters", "#1 Bundle", "6063 Extrusions",
                "Brass Radiator", "#1 HMS", "Grade 2 Old Steel (#2 2ft)", "Alternator", "Brass Cuttings",
                "Copper  Dry Bright", "85/15 Brass Scrap", "Chrome Wheels", "Copper sheet cutting",
                "Structural Steel", "Lead ingot", "Yellow Brass", "Copper cable scrap", "Lead Batteries",
                "Heater Cores", "Brass utensil scrap", "Nickel Cathode", "Lead-Solid Lead", "Romex® Wire",
                "Copper wire bars (HCL*)", "Shredded Auto Scrap", "Copper armeture", "Red Brass",
                "356 Aluminum Wheels (Clean)"
            ]
            for st in scrap_types:
                if st: db.add(MLScrapType(name=st))
                
        db.commit()
        print("✅ ML Dropdown options seeded")
    except Exception as e:
        db.rollback()
        print(f"❌ ML Dropdown seed error: {e}")
    finally:
        db.close()


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        init_db()
        print("Database initialized with pgvector")
        Base.metadata.create_all(bind=engine)
        print("Database tables created/verified")
        create_vector_indexes()
        seed_categories_if_empty()
        seed_ml_options_if_empty()

    except Exception as e:
        print(f" Database initialization error: {e}")

    init_cloudinary()


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/ping")
async def ping():
    return {"message": "pong"}