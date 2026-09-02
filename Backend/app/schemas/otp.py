from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
from enum import Enum


class OTPType(str, Enum):
    EMAIL_VERIFICATION = "EMAIL_VERIFICATION"
    PHONE_VERIFICATION = "PHONE_VERIFICATION"
    PASSWORD_RESET = "PASSWORD_RESET"


class OTPRequest(BaseModel):
    type: OTPType
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    
    @validator('email', 'phone')
    def validate_at_least_one(cls, v, values):
        if not values.get('email') and not v:
            raise ValueError('Either email or phone must be provided')
        return v


class OTPVerify(BaseModel):
    type: OTPType
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    otp: str = Field(..., min_length=4, max_length=6)
    
    @validator('otp')
    def validate_otp(cls, v):
        if not v.isdigit():
            raise ValueError('OTP must contain only digits')
        return v


class OTPResponse(BaseModel):
    message: str
    expires_in: int = 300  # 5 minutes


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=4, max_length=6)
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
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