from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from enum import Enum


class BusinessType(str, Enum):
    COMPANY = "Company"
    PARTNERSHIP = "Partnership"
    PROPRIETORSHIP = "Proprietorship"
    OTHER = "Other"


class VerificationStatus(str, Enum):
    UNVERIFIED = "Unverified"
    PENDING = "Pending"
    VERIFIED = "Verified"
    NOT_APPLICABLE = "Not Applicable"


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    business_type: BusinessType
    industry_type: Optional[str] = None
    description: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    gstin: Optional[str] = None
    
    @validator('gstin')
    def validate_gstin(cls, v):
        if v:
            # Basic GSTIN format validation (15 chars, alphanumeric)
            import re
            if not re.match(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[Z]{1}[0-9A-Z]{1}$', v):
                raise ValueError('Invalid GSTIN format')
        return v


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    business_type: Optional[BusinessType] = None
    industry_type: Optional[str] = None
    description: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    gstin: Optional[str] = None


class OrganizationResponse(BaseModel):
    id: str
    name: str
    business_type: BusinessType
    industry_type: Optional[str]
    description: Optional[str]
    location: Optional[Dict[str, Any]]
    gstin: Optional[str]
    gstin_status: VerificationStatus
    verification_status: VerificationStatus
    owner_user_id: str
    created_at: str
    updated_at: Optional[str]
    
    class Config:
        from_attributes = True