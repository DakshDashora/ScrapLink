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
from app.routers.prediction import router as prediction_router
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



def seed_categories_if_empty():
    """Seed categories if the table is empty"""
    db = SessionLocal()
    try:
        count = db.query(ScrapCategory).count()
        if count > 0:
            print(f"✅ Categories already seeded ({count} found)")
            return

        print("📂 Seeding categories...")
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
        print(f"✅ Seeded {len(categories)} categories")
    except Exception as e:
        db.rollback()
        print(f"❌ Seeding error: {e}")
    finally:
        db.close()


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        init_db()
        print("Database initialized with pgvector")

        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified")

        # ✅ Call seed function after tables are created
        seed_categories_if_empty()

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