import httpx
from app.config import settings
import random
import string


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP"""
    return ''.join(random.choices(string.digits, k=length))


async def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """
    Send an email using Brevo API (HTTPS-based)
    Works on both local and Render (port 443 is not blocked)
    """
    api_key = settings.BREVO_API_KEY
    from_email = settings.EMAIL_FROM
    
    if not api_key:
        print("❌ BREVO_API_KEY not configured")
        return False
    
    url = "https://api.brevo.com/v3/smtp/email"
    
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }
    
    payload = {
        "sender": {
            "name": "ScrapLink",
            "email": from_email
        },
        "to": [
            {"email": to_email}
        ],
        "subject": subject,
        "htmlContent": html_content
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload,
                timeout=15.0
            )
        
        if response.status_code in [200, 201, 202]:
            print(f"✅ Email sent via Brevo to {to_email}")
            return True
        else:
            print(f"❌ Brevo error {response.status_code}: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Brevo exception: {e}")
        return False


async def send_email_otp(to_email: str, otp: str, purpose: str = "verification") -> bool:
    """Send an OTP via email using Brevo"""
    subject = f"ScrapLink - Your OTP for {purpose}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4; }}
            .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .otp {{ font-size: 32px; font-weight: bold; color: #2563eb; text-align: center; padding: 20px; background: #f0f7ff; border-radius: 8px; margin: 20px 0; letter-spacing: 5px; }}
            .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2 style="color: #1e293b; text-align: center;">🔐 ScrapLink Verification</h2>
            <p style="color: #475569;">Hello,</p>
            <p style="color: #475569;">Your OTP for {purpose} is:</p>
            <div class="otp">{otp}</div>
            <p style="color: #475569;">This OTP will expire in <strong>5 minutes</strong>.</p>
            <p style="color: #475569;">If you didn't request this, please ignore this email.</p>
            <div class="footer">
                <p>ScrapLink - B2B Industrial Scrap Exchange</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return await send_email(to_email, subject, html_content)


async def send_password_reset_email(to_email: str, otp: str) -> bool:
    """Send password reset OTP via email using Brevo"""
    subject = "ScrapLink - Password Reset Request"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4; }}
            .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .otp {{ font-size: 32px; font-weight: bold; color: #dc2626; text-align: center; padding: 20px; background: #fef2f2; border-radius: 8px; margin: 20px 0; letter-spacing: 5px; }}
            .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2 style="color: #1e293b; text-align: center;">🔐 Password Reset</h2>
            <p style="color: #475569;">Hello,</p>
            <p style="color: #475569;">We received a request to reset your password. Your OTP is:</p>
            <div class="otp">{otp}</div>
            <p style="color: #475569;">This OTP will expire in <strong>5 minutes</strong>.</p>
            <p style="color: #475569;">If you didn't request this, please ignore this email.</p>
            <div class="footer">
                <p>ScrapLink - B2B Industrial Scrap Exchange</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return await send_password_reset_email_wrapper(to_email, subject, html_content)


async def send_password_reset_email_wrapper(to_email: str, subject: str, html_content: str) -> bool:
    """Wrapper for password reset (calls send_email)"""
    return await send_email(to_email, subject, html_content)