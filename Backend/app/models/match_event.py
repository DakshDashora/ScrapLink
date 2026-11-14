from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class MatchEvent(Base):
    __tablename__ = "match_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id = Column(UUID(as_uuid=True), ForeignKey("buyer_requirements.id", ondelete="CASCADE"), nullable=False, index=True)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("scrap_listings.id", ondelete="CASCADE"), nullable=False, index=True)
    
    similarity_score = Column(Numeric(5, 4), nullable=False) # e.g., 0.8543
    match_quality = Column(String, nullable=False) # e.g., "EXCELLENT_MATCH"
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    requirement = relationship("BuyerRequirement")
    listing = relationship("ScrapListing")