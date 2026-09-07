from sqlalchemy import Column, String, DateTime, ForeignKey,Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class ListingMedia(Base):
    __tablename__ = "listing_media"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("scrap_listings.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    file_type = Column(String, nullable=False)  # MIME type
    file_url = Column(String, nullable=False)   # Cloudinary URL
    public_id = Column(String, nullable=True)   # Cloudinary public ID for deletion
    
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    listing = relationship("ScrapListing", back_populates="media")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    
    def __repr__(self):
        return f"<ListingMedia {self.file_url[:30]}...>"