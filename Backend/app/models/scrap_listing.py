from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Numeric, Enum, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from enum import Enum as PyEnum


class ListingStatus(str, PyEnum):
    ACTIVE = "Active"
    RESERVED = "Reserved"
    SOLD = "Sold"
    CLOSED = "Closed"


class ListingUnit(str, PyEnum):
    KG = "kg"
    TONNE = "tonne"
    UNIT = "unit"
    METER = "meter"
    LITER = "liter"


class ScrapListing(Base):
    __tablename__ = "scrap_listings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("scrap_categories.id"), nullable=False)
    
    material_name = Column(String, nullable=False)
    grade = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    
    quantity = Column(Numeric(10, 2), nullable=False)
    unit = Column(Enum(ListingUnit), nullable=False, default=ListingUnit.KG)
    asking_price = Column(Numeric(10, 2), nullable=True)
    
    # Location
    location = Column(JSON, nullable=True)  # {address, city, state, country, pincode, latitude, longitude}
    
    # Status
    availability_status = Column(Enum(ListingStatus), nullable=False, default=ListingStatus.ACTIVE)

    view_count = Column(Integer, default=0, nullable=False)

    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    seller_org = relationship("Organization", foreign_keys=[seller_org_id])
    category = relationship("ScrapCategory")
    media = relationship("ListingMedia", back_populates="listing", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ScrapListing {self.material_name} by {self.seller_org_id}>"