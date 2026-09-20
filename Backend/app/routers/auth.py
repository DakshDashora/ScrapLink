from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.user import User, UserRole
from app.security import (
    get_password_hash, verify_password, create_access_token,
    validate_password, get_current_user
)
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse
from app.routers.otp import generate_and_send_otp
from app.models.otp import OTPType
from app.config import settings
import uuid

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user
    
    - Email must be unique
    - Phone must be unique
    - Password must be 8+ chars with uppercase, lowercase, and digits
    - Role can be Buyer, Seller, or Admin
    - Email OTP is auto-sent after registration
    """
    # Validate password
    if not validate_password(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters with uppercase, lowercase, and digits"
        )
    
    # Check if email exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if phone exists
    existing_phone = db.query(User).filter(User.phone == user_data.phone).first()
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    # Create user with verification status = FALSE
    hashed_password = get_password_hash(user_data.password)
    user = User(
        id=uuid.uuid4(),
        full_name=user_data.full_name,
        email=user_data.email,
        password_hash=hashed_password,
        phone=user_data.phone,
        role=UserRole(user_data.role.value),
        email_verified=False,
        phone_verified=False
    )
    
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database error creating user"
        )
    
    # 🔥 AUTO-SEND EMAIL VERIFICATION OTP
    try:
        sent, otp_code = await generate_and_send_otp(user, OTPType.EMAIL_VERIFICATION, db)
        if not sent:
            print(f"⚠️ Warning: Failed to send email OTP to {user.email}")
    except Exception as e:
        print(f"⚠️ Error sending email OTP: {e}")
    
    # Return user with verification status
    return UserResponse(
        id=str(user.id),
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        role=user.role,
        email_verified=user.email_verified,
        phone_verified=user.phone_verified,
        created_at=user.created_at.isoformat() if user.created_at else None
    )


@router.post("/login", response_model=TokenResponse)
async def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Login and receive JWT token
    
    Requirements:
    - Email must be verified
    - Phone must be verified
    """
    user = db.query(User).filter(User.email == user_data.email).first()
    
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # ✅ Check email verification (MANDATORY for everyone)
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your email for the verification OTP.",
            headers={"X-Verification-Required": "email"}
        )
    
    # ✅ Check phone verification (MANDATORY for everyone)
    if not user.phone_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Phone not verified. Please check your phone for the verification OTP.",
            headers={"X-Verification-Required": "phone"}
        )
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "email_verified": user.email_verified,
            "phone_verified": user.phone_verified
        }
    )
    
    return TokenResponse(
        access_token=access_token,
        user_id=str(user.id),
        email=user.email,
        role=user.role,
        email_verified=user.email_verified,
        phone_verified=user.phone_verified,
        full_name=user.full_name
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user"""
    return UserResponse(
        id=str(current_user.id),
        full_name=current_user.full_name,
        email=current_user.email,
        phone=current_user.phone,
        role=current_user.role,
        email_verified=current_user.email_verified,
        phone_verified=current_user.phone_verified,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None
    )


@router.get("/verification-status")
async def get_verification_status(current_user: User = Depends(get_current_user)):
    """Get current user's verification status"""
    return {
        "email_verified": current_user.email_verified,
        "phone_verified": current_user.phone_verified,
        "fully_verified": current_user.email_verified and current_user.phone_verified,
        "next_step": None if (current_user.email_verified and current_user.phone_verified) 
                    else ("EMAIL_VERIFICATION" if not current_user.email_verified 
                    else "PHONE_VERIFICATION")
    }