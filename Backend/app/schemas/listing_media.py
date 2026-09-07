from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MediaUploadRequest(BaseModel):
    listing_id: str
    file_type: str
    file_url: str
    public_id: Optional[str] = None
    is_primary: bool = False


class MediaResponse(BaseModel):
    id: str
    listing_id: str
    file_type: str
    file_url: str
    is_primary: bool
    created_at: str
    
    class Config:
        from_attributes = True