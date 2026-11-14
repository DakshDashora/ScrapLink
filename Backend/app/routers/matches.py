from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
import httpx
import uuid

from app.database import get_db
from app.config import settings
from app.security import get_current_user
from app.models.user import User
from app.models.buyer_requirement import BuyerRequirement, RequirementStatus
from app.models.scrap_listing import ScrapListing, ListingStatus
from app.schemas.match import MatchRankRequest, MatchRankResponse, CandidateListing

router = APIRouter(prefix="/api/matches", tags=["Semantic Matching"])

@router.post("/{requirement_id}/refresh", response_model=MatchRankResponse)
async def refresh_matches(
    requirement_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate ranked matches for a requirement by calling Daksh's ML service"""
    
    # 1. Fetch the requirement
    req = db.query(BuyerRequirement).filter(BuyerRequirement.id == uuid.UUID(requirement_id)).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # 2. Fetch candidate listings (Hard Filter: Active only)
    # We fetch active listings and let Daksh rank them
    listings = db.query(ScrapListing).filter(
        ScrapListing.availability_status == ListingStatus.ACTIVE
    ).limit(100).all() # Limit to 100 to avoid huge payloads

    if not listings:
        raise HTTPException(status_code=400, detail="No active listings to match against")

    # 3. Format the requirement text
    req_text = f"Need {req.quantity} {req.unit} of {req.material_name}."
    if req.grade: req_text += f" Grade: {req.grade}."
    if req.description: req_text += f" Details: {req.description}."

    # 4. Format the candidate listings for Daksh
    candidates = []
    for l in listings:
        candidates.append(CandidateListing(
            id=str(l.id),
            material_name=l.material_name,
            category=str(l.category_id), # Or l.category.name if joined
            grade=l.grade,
            description=l.description,
            quantity=float(l.quantity),
            unit=l.unit.value,
            asking_price=float(l.asking_price) if l.asking_price else None,
            availability_status=l.availability_status.value
        ))

    # 5. Call Daksh's ML Service
    if not settings.ML_SERVICE_URL or not settings.ML_JOB_TOKEN:
        raise HTTPException(status_code=503, detail="Matching service not configured")

    ml_url = f"{settings.ML_SERVICE_URL.rstrip('/')}/matches/rank"
    payload = MatchRankRequest(
        requirement_text=req_text,
        candidate_listings=candidates,
        top_k=10,
        min_similarity=0.30,
        enforce_active_only=True
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                ml_url,
                json=payload.model_dump(exclude_none=True),
                headers={"X-ML-Job-Token": settings.ML_JOB_TOKEN}
            )
            
        if response.status_code == 200:
            # TODO: Save the top_matches to a `match_events` table here in the future
            return response.json()
            
        raise HTTPException(status_code=502, detail="ML service returned an error")
        
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Could not reach matching service")