from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from enum import Enum
import re

class UserRole(str, Enum):
    BUYER = "Buyer"
    SELLER = "Seller"
    ADMIN = "Admin"

class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: UserRole
    gstin: Optional[str] = None

    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        return v

    @field_validator('gstin')
    def validate_gstin(cls, v, info):
        if info.data.get('role') == UserRole.SELLER and not v:
            raise ValueError('GSTIN is mandatory for Seller registration')
        if v:
            if not re.match(r'^[0-9A-Z]{15}$', v):
                raise ValueError('GSTIN must be 15 alphanumeric characters')
        return v

class RegisterResponse(BaseModel):
    status: str
    message: str
    user_id: int
    email: str
    role: UserRole

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int