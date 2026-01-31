from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    PROJECT_NAME: str = "TeleGuard"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database (Neon/Postgres)
    DATABASE_URL: str = Field(validation_alias=AliasChoices("DATABASE_URL", "POSTGRES_URL"))
    
    # Security
    SECRET_KEY: str = Field(validation_alias=AliasChoices("SECRET_KEY", "SECRET"))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Hardening
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]
    
    # External
    TELEGRAM_API_ID: Optional[int] = None
    TELEGRAM_API_HASH: Optional[str] = None
    BOT_TOKEN: Optional[str] = None
    
    # Email
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None

    # Defaults
    INVITE: Optional[str] = None
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }

settings = Settings()
