from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.otp import OTPRecord, OTPType
from app.security import get_password_hash, verify_password
from app.schemas.otp import (
    OTPRequest, OTPVerify, OTPResponse,
    PasswordResetRequest, PasswordResetConfirm
)
from app.utils.email import generate_otp, send_email_otp, send_password_reset_email
from app.utils.sms import send_sms_otp
import uuid

router = APIRouter(prefix="/auth/otp", tags=["OTP Verification"])

async def generate_and_send_otp(user: User, otp_type: OTPType, db: Session):
    """
    Internal function to generate and send OTP
    """
    # Generate OTP
    otp_code = generate_otp()
    otp_hash = get_password_hash(otp_code)
    
    # Print for debugging
    print(f"\n{'='*60}")
    print(f"🔥 OTP GENERATED: {otp_type.value}")
    print(f"{'='*60}")
    print(f"🔑 OTP CODE: {otp_code}")
    print(f"👤 User: {user.email}")
    print(f"{'='*60}\n")
    
    # Delete old expired OTPs
    db.query(OTPRecord).filter(
        OTPRecord.user_id == user.id,
        OTPRecord.type == otp_type,
        OTPRecord.expires_at < datetime.utcnow()
    ).delete()
    
    # Store in database
    otp_record = OTPRecord(
        id=uuid.uuid4(),
        user_id=user.id,
        otp_hash=otp_hash,
        type=otp_type,
        expires_at=datetime.utcnow() + timedelta(minutes=5),
        attempt_count=0
    )
    
    db.add(otp_record)
    db.commit()
    db.refresh(otp_record)
    
    # Send via appropriate channel
    sent = False
    
    if otp_type == OTPType.EMAIL_VERIFICATION:
        # ✅ AWAIT the async function
        sent = await send_email_otp(user.email, otp_code, "email verification")
        if sent:
            print(f"✅ Email OTP sent to {user.email}")
        else:
            print(f"❌ Failed to send email OTP to {user.email}")
    
    elif otp_type == OTPType.PHONE_VERIFICATION:
        sent = send_sms_otp(user.phone, otp_code)
        print(f"📱 MOCK SMS OTP for {user.phone}: {otp_code}")
    
    elif otp_type == OTPType.PASSWORD_RESET:
        # ✅ AWAIT the async function
        sent = await send_password_reset_email(user.email, otp_code)
        if sent:
            print(f"✅ Password reset email sent to {user.email}")
        else:
            print(f"❌ Failed to send password reset email to {user.email}")
    
    return sent, otp_code

# ============================================
# REQUEST OTP ENDPOINT (No Auth Required)
# ============================================
@router.post("/request", response_model=OTPResponse)
async def request_otp(
    otp_request: OTPRequest,
    db: Session = Depends(get_db)
):
    """Request OTP for verification - No authentication required"""
    
    print(f"\n OTP REQUEST RECEIVED: {otp_request.type.value}")
    
    user = None
    if otp_request.email:
        user = db.query(User).filter(User.email == otp_request.email).first()
        print(f" Looking up user by email: {otp_request.email}")
    elif otp_request.phone:
        user = db.query(User).filter(User.phone == otp_request.phone).first()
        print(f" Looking up user by phone: {otp_request.phone}")
    
    if not user:
        print(f" User not found for {otp_request.email or otp_request.phone}")
        return OTPResponse(
            message="OTP sent successfully if account exists",
            expires_in=300
        )
    
    print(f" User found: {user.email}")
    sent, otp_code = await generate_and_send_otp(user, otp_request.type, db)
    
    return OTPResponse(
        message="OTP sent successfully",
        expires_in=300
    )


@router.post("/resend", response_model=OTPResponse)
async def resend_otp(
    otp_request: OTPRequest,
    db: Session = Depends(get_db)
):
    
    print(f"\n OTP RESEND REQUESTED: {otp_request.type.value}")
    
    user = None
    if otp_request.email:
        user = db.query(User).filter(User.email == otp_request.email).first()
    elif otp_request.phone:
        user = db.query(User).filter(User.phone == otp_request.phone).first()
    
    if not user:
        print(f" User not found")
        return OTPResponse(
            message="OTP resent successfully",
            expires_in=300
        )
    
    db.query(OTPRecord).filter(
        OTPRecord.user_id == user.id,
        OTPRecord.type == otp_request.type,
        OTPRecord.expires_at < datetime.utcnow()
    ).delete()
    db.commit()
    
    sent, otp_code = await generate_and_send_otp(user, otp_request.type, db)
    
    return OTPResponse(
        message="OTP resent successfully",
        expires_in=300
    )


@router.post("/verify")
async def verify_otp(
    otp_verify: OTPVerify,
    db: Session = Depends(get_db)
):
    
    print(f"\n OTP VERIFICATION REQUESTED")
    print(f"Type: {otp_verify.type.value}")
    
    user = None
    if otp_verify.email:
        user = db.query(User).filter(User.email == otp_verify.email).first()
        print(f" Looking up user by email: {otp_verify.email}")
    elif otp_verify.phone:
        user = db.query(User).filter(User.phone == otp_verify.phone).first()
        print(f" Looking up user by phone: {otp_verify.phone}")
    
    if not user:
        print(f" User not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    print(f" User found: {user.email}")
    
    otp_record = db.query(OTPRecord).filter(
        OTPRecord.user_id == user.id,
        OTPRecord.type == otp_verify.type,
        OTPRecord.verified_at.is_(None),
        OTPRecord.expires_at > datetime.utcnow()
    ).order_by(OTPRecord.created_at.desc()).first()
    
    if not otp_record:
        print(f" No valid OTP found for {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    print(f" Found OTP record for {user.email}")
    
    if otp_record.attempt_count >= 5:
        print(f" Too many attempts for {user.email}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please request a new OTP."
        )
    
    if not verify_password(otp_verify.otp, otp_record.otp_hash):
        otp_record.attempt_count += 1
        db.commit()
        print(f" Invalid OTP entered for {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )
    
    print(f" OTP verified successfully for {user.email}")
    
    otp_record.verified_at = datetime.utcnow()
    otp_record.attempt_count += 1
    
    if otp_verify.type == OTPType.EMAIL_VERIFICATION:
        user.email_verified = True
        db.commit()
        
        print(f"✅ Email verified for {user.email}")
        print(f"📱 Now auto-sending PHONE OTP...")
        
        sent, otp_code =await generate_and_send_otp(user, OTPType.PHONE_VERIFICATION, db)
        
        return {
            "message": " Email verified successfully! Phone OTP has been sent (MOCK - check console).",
            "email_verified": user.email_verified,
            "phone_verified": user.phone_verified,
            "next_step": "PHONE_VERIFICATION"
        }
    
    elif otp_verify.type == OTPType.PHONE_VERIFICATION:
        user.phone_verified = True
        db.commit()
        
        print(f" Phone verified for {user.email}")
        print(f" User is now fully verified!")
        
        return {
            "message": " Phone verified successfully! You can now login.",
            "email_verified": user.email_verified,
            "phone_verified": user.phone_verified,
            "next_step": "LOGIN_READY"
        }
    
    elif otp_verify.type == OTPType.PASSWORD_RESET:
        db.commit()
        return {
            "message": " OTP verified successfully. You can now reset your password.",
            "next_step": "RESET_PASSWORD"
        }


@router.post("/password-reset-request")
async def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset OTP (REAL EMAIL)"""
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        return {"message": "Password reset OTP sent if email exists"}
    
    sent, otp_code =await generate_and_send_otp(user, OTPType.PASSWORD_RESET, db)
    
    return {"message": "Password reset OTP sent if email exists"}


@router.post("/password-reset-confirm")
async def confirm_password_reset(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset with OTP"""
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    otp_record = db.query(OTPRecord).filter(
        OTPRecord.user_id == user.id,
        OTPRecord.type == OTPType.PASSWORD_RESET,
        OTPRecord.verified_at.is_(None),
        OTPRecord.expires_at > datetime.utcnow()
    ).order_by(OTPRecord.created_at.desc()).first()
    
    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    if not verify_password(request.otp, otp_record.otp_hash):
        otp_record.attempt_count += 1
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )
    
    from app.security import validate_password, get_password_hash
    if not validate_password(request.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters with uppercase, lowercase, and digits"
        )
    
    user.password_hash = get_password_hash(request.new_password)
    otp_record.verified_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Password reset successfully"}