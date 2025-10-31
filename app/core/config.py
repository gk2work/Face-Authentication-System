"""Application configuration management"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # MongoDB Configuration
    MONGODB_URI: str
    MONGODB_DATABASE: str = "face_auth_db"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: Optional[str] = None
    
    # Storage Configuration
    STORAGE_PATH: str = "./storage/photographs"
    VECTOR_DB_PATH: str = "./storage/vectors"
    
    # Face Recognition Configuration
    FACE_MODEL: str = "facenet"
    VERIFICATION_THRESHOLD: float = 0.85
    EMBEDDING_DIMENSION: int = 512
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    
    # Security Configuration
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Performance Configuration
    MAX_QUEUE_SIZE: int = 10000
    PROCESSING_TIMEOUT: int = 10
    CACHE_TTL: int = 3600
    
    # Monitoring Configuration
    LOG_LEVEL: str = "INFO"
    ENABLE_METRICS: bool = True
    
    # Quality Thresholds
    MIN_FACE_SIZE: int = 80
    BLUR_THRESHOLD: float = 100.0
    QUALITY_SCORE_THRESHOLD: float = 0.7
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
