from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import auth_router, otp_router, org_router, listings_router  
from app.config import settings
from app.utils.cloudinary_service import init_cloudinary  

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


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        init_db()
        print("Database initialized with pgvector")
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