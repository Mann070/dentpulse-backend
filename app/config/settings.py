from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "DentPulse AI"
    DATABASE_URL: str = "sqlite+aiosqlite:///./dentpulse.db"
    SECRET_KEY: str = "clinical_intelligence_secret_key_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    UPLOAD_DIR: str = "uploads"

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

@lru_cache()
def get_settings():
    return Settings()
