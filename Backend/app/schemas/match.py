from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class CandidateListing(BaseModel):
    id: str
    material_name: str
    category: Optional[str] = None
    grade: Optional[str] = None
    description: Optional[str] = None
    quantity: float
    unit: str = "kg"
    asking_price: Optional[float] = None
    availability_status: Optional[str] = None
    location: Optional[Dict[str, Any]] = None

class MatchRankRequest(BaseModel):
    requirement_text: str
    candidate_listings: List[CandidateListing]
    top_k: int = 10
    min_similarity: float = 0.30
    enforce_active_only: bool = True

class RankedMatch(BaseModel):
    listing_id: str
    material_name: str
    category: Optional[str]
    grade: Optional[str]
    quantity: float
    unit: str
    asking_price: Optional[float]
    location: Optional[Dict[str, Any]]
    similarity_score: float
    match_quality: str
    hard_constraints_passed: bool

class MatchRankResponse(BaseModel):
    status: str
    total_candidates_evaluated: int
    matches_found: int
    top_matches: List[RankedMatch]
    model_version: str
    disclaimer: str