from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from app.database import get_db
from app.models.scrap_listing import ScrapListing
from app.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/trust", tags=["Trust & Anomaly"])

@router.get("/{listing_id}")
async def get_listing_trust(
    listing_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch anomaly/trust result for a listing.
    (Placeholder until Daksh's Isolation Forest API is ready)
    """
    try:
        listing_uuid = uuid.UUID(listing_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid listing ID format")

    listing = db.query(ScrapListing).filter(ScrapListing.id == listing_uuid).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # TODO: Call Daksh's ML service here once ready.
    # For now, return a standard "Normal" indicator so Anushka can build the UI.
    
    return {
        "listing_id": str(listing.id),
        "status": "success",
        "indicator": "NORMAL", 
        "score": 0.05,         
        "explanation": "This listing follows standard pricing and activity patterns.",
        "model_version": "v1-placeholder",
        "is_fraud_probability": False
    }