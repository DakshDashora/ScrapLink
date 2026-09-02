import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings
import random
import string
import re


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP"""
    return ''.join(random.choices(string.digits, k=length))


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send a real email using SMTP"""
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = settings.EMAIL_FROM
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(html_content, 'html'))
        
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False


def send_email_otp(to_email: str, otp: str, purpose: str = "verification") -> bool:
    """Send a real OTP via email"""
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
            .header {{ color: #1e293b; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2 class="header">🔐 ScrapLink Verification</h2>
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
    
    return send_email(to_email, subject, html_content)


def send_password_reset_email(to_email: str, otp: str) -> bool:
    """Send password reset OTP via email"""
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
            <p style="color: #475569;">If you didn't request this, please ignore this email and your password will remain unchanged.</p>
            <div class="footer">
                <p>ScrapLink - B2B Industrial Scrap Exchange</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, html_content)