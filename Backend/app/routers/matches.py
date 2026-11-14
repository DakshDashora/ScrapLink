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
from app.models.match_event import MatchEvent
from app.schemas.match import RankedMatch


router = APIRouter(prefix="/api/matches", tags=["Semantic Matching"])

@router.post("/{requirement_id}/refresh", response_model=MatchRankResponse)
async def refresh_matches(
    requirement_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate ranked matches for a requirement by calling Daksh's ML service"""
    
    req = db.query(BuyerRequirement).filter(BuyerRequirement.id == uuid.UUID(requirement_id)).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    listings = db.query(ScrapListing).filter(
        ScrapListing.availability_status == ListingStatus.ACTIVE
    ).limit(100).all() 

    if not listings:
        raise HTTPException(status_code=400, detail="No active listings to match against")

    req_text = f"Need {req.quantity} {req.unit} of {req.material_name}."
    if req.grade: req_text += f" Grade: {req.grade}."
    if req.description: req_text += f" Details: {req.description}."

    # 4. Format the candidate listings for Daksh
    candidates = []
    for l in listings:
        candidates.append(CandidateListing(
            id=str(l.id),
            material_name=l.material_name,
            category=str(l.category_id), 
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
            result = response.json()
            
            matches = result.get("top_matches", [])
            for m in matches:
                event = MatchEvent(
                    id=uuid.uuid4(),
                    requirement_id=req.id,
                    listing_id=uuid.UUID(m["listing_id"]),
                    similarity_score=m["similarity_score"],
                    match_quality=m["match_quality"]
                )
                db.add(event)
            db.commit()
            
            return result
            
        raise HTTPException(status_code=502, detail="ML service returned an error")
        
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Could not reach matching service")

@router.get("/{requirement_id}", response_model=MatchRankResponse)
async def get_matches(
    requirement_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch saved matches for a requirement"""
    req = db.query(BuyerRequirement).filter(BuyerRequirement.id == uuid.UUID(requirement_id)).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    events = db.query(MatchEvent).filter(
        MatchEvent.requirement_id == req.id
    ).order_by(MatchEvent.similarity_score.desc()).all()

    if not events:
        raise HTTPException(status_code=404, detail="No matches found. Call /refresh first.")

    top_matches = []
    for e in events:
        listing = db.query(ScrapListing).filter(ScrapListing.id == e.listing_id).first()
        if listing:
            top_matches.append({
                "listing_id": str(listing.id),
                "material_name": listing.material_name,
                "category": "Unknown", # You can join to get category name
                "grade": listing.grade,
                "quantity": float(listing.quantity),
                "unit": listing.unit.value,
                "asking_price": float(listing.asking_price) if listing.asking_price else None,
                "location": listing.location,
                "similarity_score": float(e.similarity_score),
                "match_quality": e.match_quality,
                "hard_constraints_passed": True
            })

    return {
        "status": "success",
        "total_candidates_evaluated": len(events),
        "matches_found": len(events),
        "top_matches": top_matches,
        "model_version": "sbert-all-MiniLM-L6-v2-v1",
        "disclaimer": "Semantic matches are decision-support suggestions."
    }


@router.get("/match-alerts")
async def get_match_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch recent match alerts for the buyer's organization"""
    # Get buyer's org
    from app.models.organization_member import OrganizationMember
    org = db.query(OrganizationMember).filter(OrganizationMember.user_id == current_user.id).first()
    if not org:
        raise HTTPException(status_code=400, detail="No organization found")

    # Get requirements for this org
    reqs = db.query(BuyerRequirement).filter(BuyerRequirement.buyer_org_id == org.organization_id).all()
    req_ids = [r.id for r in reqs]

    # Get recent matches for these requirements
    events = db.query(MatchEvent).filter(
        MatchEvent.requirement_id.in_(req_ids)
    ).order_by(MatchEvent.created_at.desc()).limit(20).all()

    alerts = []
    for e in events:
        listing = db.query(ScrapListing).filter(ScrapListing.id == e.listing_id).first()
        if listing:
            alerts.append({
                "id": str(e.id),
                "requirement_id": str(e.requirement_id),
                "listing_id": str(e.listing_id),
                "listing_name": listing.material_name,
                "similarity_score": float(e.similarity_score),
                "created_at": e.created_at.isoformat()
            })

    return {"status": "success", "alerts": alerts, "total": len(alerts)}