from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    BUYER = "Buyer"
    SELLER = "Seller"
    ADMIN = "Admin"


class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    phone: str = Field(..., min_length=10, max_length=15)  # ✅ Required now
    role: UserRole = UserRole.BUYER
    
    @validator('password')
    def validate_password(cls, v):
        import re
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        import re
        # Basic phone validation - accepts +91XXXXXXXXXX or 10 digits
        if not re.match(r'^\+?[0-9]{10,15}$', v):
            raise ValueError('Phone number must be 10-15 digits, optionally starting with +')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: UserRole
    email_verified: bool
    phone_verified: bool
    full_name: str


class UserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    phone: Optional[str]
    role: UserRole
    email_verified: bool
    phone_verified: bool
    created_at: Optional[str]
    
    class Config:
        from_attributes = True