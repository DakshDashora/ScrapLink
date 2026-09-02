# from twilio.rest import Client
# from app.config import settings
# import random
# import string


# def generate_otp(length: int = 6) -> str:
#     """Generate a numeric OTP"""
#     return ''.join(random.choices(string.digits, k=length))


# def send_sms_otp(to_phone: str, otp: str) -> bool:
#     """Send OTP via Twilio SMS"""
#     try:
#         if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, 
#                    settings.TWILIO_VERIFY_SERVICE_SID]):
#             print("Twilio not configured, skipping SMS")
#             return False
        
#         client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
#         # Use Twilio Verify Service
#         verification = client.verify.v2.services(
#             settings.TWILIO_VERIFY_SERVICE_SID
#         ).verifications.create(
#             to=to_phone,
#             channel="sms"
#         )
        
#         return verification.status == "pending"
#     except Exception as e:
#         print(f"SMS error: {e}")
#         return False


# def verify_phone_otp(to_phone: str, otp: str) -> bool:
#     """Verify OTP using Twilio Verify Service"""
#     try:
#         if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, 
#                    settings.TWILIO_VERIFY_SERVICE_SID]):
#             return False
        
#         client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
#         verification_check = client.verify.v2.services(
#             settings.TWILIO_VERIFY_SERVICE_SID
#         ).verification_checks.create(
#             to=to_phone,
#             code=otp
#         )
        
#         return verification_check.status == "approved"
#     except Exception as e:
#         print(f"SMS verification error: {e}")
#         return False


from app.config import settings
import random
import string


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP"""
    return ''.join(random.choices(string.digits, k=length))


def send_sms_otp(to_phone: str, otp: str) -> bool:
    """
    Send OTP via SMS
    ⚠️ Currently in MOCK MODE - OTP is logged to console
    """
    # ✅ ALWAYS MOCK for SMS - logs to console
    print(f"\n{'='*60}")
    print(f"📱 MOCK SMS OTP (Phone Verification)")
    print(f"{'='*60}")
    print(f"To: {to_phone}")
    print(f"📱 Your OTP is: {otp}")
    print(f"⏰ Expires in: 5 minutes")
    print(f"{'='*60}\n")
    return True


def verify_phone_otp(to_phone: str, otp: str) -> bool:
    """
    Verify OTP
    In mock mode, verification is handled by the database
    """
    # In mock mode, verification is done in the verify_otp endpoint
    # using the stored hash in database
    return True