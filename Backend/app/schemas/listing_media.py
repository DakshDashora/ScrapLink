from pydantic import BaseModel, Field
from typing import Optional,List
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
    public_id: Optional[str]
    is_primary: bool
    created_at: str
    
    class Config:
        from_attributes = True

class MediaUploadResponse(BaseModel):
    message: str
    media: MediaResponse


class MediaListResponse(BaseModel):
    media: List[MediaResponse]
    total: int


class SetPrimaryMedia(BaseModel):
    media_id: str