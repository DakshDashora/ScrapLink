from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any,List
from enum import Enum
from datetime import datetime
from decimal import Decimal


class ListingStatus(str, Enum):
    ACTIVE = "Active"
    RESERVED = "Reserved"
    SOLD = "Sold"
    CLOSED = "Closed"


class ListingUnit(str, Enum):
    KG = "kg"
    TONNE = "tonne"
    UNIT = "unit"
    METER = "meter"
    LITER = "liter"


class ListingCreate(BaseModel):
    category_id: str
    material_name: str = Field(..., min_length=1, max_length=100)
    grade: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit: ListingUnit = ListingUnit.KG
    asking_price: Optional[Decimal] = Field(None, gt=0)
    location: Optional[Dict[str, Any]] = None


class ListingUpdate(BaseModel):
    category_id: Optional[str] = None
    material_name: Optional[str] = Field(None, min_length=1, max_length=100)
    grade: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit: Optional[ListingUnit] = None
    asking_price: Optional[Decimal] = Field(None, gt=0)
    location: Optional[Dict[str, Any]] = None
    availability_status: Optional[ListingStatus] = None


class ListingResponse(BaseModel):
    id: str
    seller_org_id: str
    seller_org_name: str
    category_id: str
    category_name: str
    material_name: str
    grade: Optional[str]
    description: Optional[str]
    quantity: str
    unit: ListingUnit
    asking_price: Optional[str]
    location: Optional[Dict[str, Any]]
    availability_status: ListingStatus
    created_at: str
    updated_at: Optional[str]
    media: list = []  # Will contain media URLs
    
    class Config:
        from_attributes = True


class ListingListResponse(BaseModel):
    items: list[ListingResponse]
    total: int
    page: int
    size: int
    pages: int


class ListingSearchParams(BaseModel):
    category_id: Optional[str] = None
    material_name: Optional[str] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    min_quantity: Optional[Decimal] = None
    max_quantity: Optional[Decimal] = None
    unit: Optional[ListingUnit] = None
    status: Optional[ListingStatus] = ListingStatus.ACTIVE
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[float] = None
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[str] = "desc"

class ListingListResponse(BaseModel):
    items: List[ListingResponse]
    total: int
    page: int
    size: int
    pages: int