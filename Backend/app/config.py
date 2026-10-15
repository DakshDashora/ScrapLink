from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    
    # Server
    APP_NAME: str = "ScrapLink"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    BREVO_API_KEY: Optional[str] = None
    
    # Email (REAL - Required for email OTP)
    EMAIL_HOST: str
    EMAIL_PORT: int = 587
    EMAIL_USERNAME: str
    EMAIL_PASSWORD: str
    EMAIL_FROM: str
    
    # Twilio (OPTIONAL - Not needed for SMS mock)
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_VERIFY_SERVICE_SID: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None

    # ✅ Cloudinary
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None

    ML_SERVICE_URL: Optional[str] = None
    ML_JOB_TOKEN: Optional[str] = None
    
    # ML/Data
    COMMODITY_DATA_PATH: str = "./data/commodity_data.csv"
    MCX_DATA_ENABLED: bool = True
    WORLD_BANK_DATA_ENABLED: bool = True
    MODEL_PATH: str = "./models/"
    
    @property
    def origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()