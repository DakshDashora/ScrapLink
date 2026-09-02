from sqlalchemy import Column, String, Text, DateTime, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from enum import Enum as PyEnum


class BusinessType(str, PyEnum):
    COMPANY = "Company"
    PARTNERSHIP = "Partnership"
    PROPRIETORSHIP = "Proprietorship"
    OTHER = "Other"


class VerificationStatus(str, PyEnum):
    UNVERIFIED = "Unverified"
    PENDING = "Pending"
    VERIFIED = "Verified"
    NOT_APPLICABLE = "Not Applicable"


class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    business_type = Column(Enum(BusinessType), nullable=False)
    industry_type = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    location = Column(JSON, nullable=True)  # Address and geo data
    
    # GST Information
    gstin = Column(String, nullable=True, index=True)
    gstin_status = Column(Enum(VerificationStatus), default=VerificationStatus.UNVERIFIED)
    
    # Verification
    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.UNVERIFIED)
    
    # Owner
    owner_user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Organization {self.name}>"