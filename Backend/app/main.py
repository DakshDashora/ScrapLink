from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv

from app.database import init_db
from app.routers import auth

load_dotenv()

app = FastAPI(
    title="ScrapLink API",
    description="AI-Driven B2B Industrial Scrap Exchange Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)

@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
async def health_check():
    return {
        "status": "healthy",
        "service": "ScrapLink API",
        "version": "0.1.0"
    }

@app.get("/ping")
async def ping():
    return {"ping": "pong"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "True").lower() == "true"
    )