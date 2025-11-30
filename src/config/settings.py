"""
Uygulama Ayarları
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Uygulama yapılandırması"""

    # Uygulama
    APP_NAME: str = "Friendship AI Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # API
    API_PREFIX: str = "/api/v1"

    # Ollama (Yerel LLM - Ücretsiz)
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:1b"

    # Veritabanı
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/friendship_ai"

    # Redis (oturum ve önbellek için)
    REDIS_URL: str = "redis://localhost:6379"

    # JWT
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # Analiz ayarları
    MIN_MESSAGES_FOR_ANALYSIS: int = 30
    MIN_CONFIDENCE_FOR_MATCHING: float = 0.6
    MAX_MATCHES_PER_USER: int = 10

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
