import cloudinary
import cloudinary.uploader
import cloudinary.api
from app.config import settings
from typing import Optional, Dict
import uuid


def init_cloudinary():
    """Initialize Cloudinary with credentials"""
    if not all([
        settings.CLOUDINARY_CLOUD_NAME,
        settings.CLOUDINARY_API_KEY,
        settings.CLOUDINARY_API_SECRET
    ]):
        print("Cloudinary not configured. Image upload will not work.")
        return False
    
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True
    )
    print(" Cloudinary initialized")
    return True


def upload_image(file_bytes: bytes, folder: str = "scraplink/listings") -> Optional[Dict]:
    """
    Upload an image to Cloudinary
    
    Returns: Dict with url, public_id, format, etc.
    """
    try:
        # Generate unique public_id
        filename = f"{uuid.uuid4()}"
        
        # Upload
        result = cloudinary.uploader.upload(
            file_bytes,
            folder=folder,
            public_id=filename,
            resource_type="image",
            transformation=[
                {"width": 1200, "height": 1200, "crop": "limit"},
                {"quality": "auto"},
                {"fetch_format": "auto"}
            ]
        )
        
        return {
            "url": result.get("secure_url"),
            "public_id": result.get("public_id"),
            "format": result.get("format"),
            "width": result.get("width"),
            "height": result.get("height"),
            "bytes": result.get("bytes")
        }
    
    except Exception as e:
        print(f" Cloudinary upload error: {e}")
        return None


def delete_image(public_id: str) -> bool:
    """
    Delete an image from Cloudinary
    
    Returns: True if successful
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        return result.get("result") == "ok"
    except Exception as e:
        print(f" Cloudinary delete error: {e}")
        return False


def generate_thumbnail(public_id: str, width: int = 300, height: int = 300) -> str:
    """Generate a thumbnail URL from a public_id"""
    try:
        url = cloudinary.CloudinaryImage(public_id).build_url(
            width=width,
            height=height,
            crop="fill",
            quality="auto",
            fetch_format="auto"
        )
        return url
    except Exception as e:
        print(f" Cloudinary thumbnail error: {e}")
        return ""