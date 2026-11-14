from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from enum import Enum
from decimal import Decimal

class RequirementStatus(str, Enum):
    OPEN = "Open"
    MATCHED = "Matched"
    CLOSED = "Closed"

class RequirementUnit(str, Enum):
    KG = "kg"
    TONNE = "tonne"
    UNIT = "unit"
    METER = "meter"
    LITER = "liter"


class RequirementCreate(BaseModel):
    category_id: str
    material_name: str = Field(..., min_length=1, max_length=100)
    grade: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit: RequirementUnit = RequirementUnit.KG
    target_price: Optional[Decimal] = Field(None, gt=0)
    location: Optional[Dict[str, Any]] = None


class RequirementUpdate(BaseModel):
    category_id: Optional[str] = None
    material_name: Optional[str] = Field(None, min_length=1, max_length=100)
    grade: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit: Optional[RequirementUnit] = None
    target_price: Optional[Decimal] = Field(None, gt=0)
    location: Optional[Dict[str, Any]] = None
    status: Optional[RequirementStatus] = None


class RequirementResponse(BaseModel):
    id: str
    buyer_org_id: str
    buyer_org_name: str
    category_id: str
    category_name: str
    material_name: str
    grade: Optional[str]
    description: Optional[str]
    quantity: str
    unit: RequirementUnit
    target_price: Optional[str]
    location: Optional[Dict[str, Any]]
    status: RequirementStatus
    created_at: str
    updated_at: Optional[str]
    
    class Config:
        from_attributes = True


class RequirementListResponse(BaseModel):
    items: list[RequirementResponse]
    total: int
    page: int
    size: int
    pages: int