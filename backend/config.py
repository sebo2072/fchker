"""
Configuration management for the fact-checker application.
Loads settings from environment variables with validation.
"""
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


# Determine the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # GCP Configuration
    gcp_project_id: str = Field(default="", env="GCP_PROJECT_ID")
    gcp_location: str = Field(default="us-central1", env="GCP_LOCATION")
    google_application_credentials: str = Field(
        default=str(BASE_DIR / "key" / "service-account-key.json"),
        env="GOOGLE_APPLICATION_CREDENTIALS"
    )
    
    # Vertex AI Configuration
    gemini_model: str = Field(
        default="gemini-2.0-flash-thinking-exp-01-21",
        env="GEMINI_MODEL"
    )
    gemini_fast_model: str = Field(
        default="gemini-1.5-flash",
        env="GEMINI_FAST_MODEL"
    )
    gemini_temperature: float = Field(default=0.1, env="GEMINI_TEMPERATURE")
    gemini_max_output_tokens: int = Field(default=2048, env="GEMINI_MAX_OUTPUT_TOKENS")
    thinking_level: str = Field(default="HIGH", env="THINKING_LEVEL")
    include_thoughts: bool = Field(default=True, env="INCLUDE_THOUGHTS")
    
    # OpenAI Configuration (for fast refinement)
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    openai_refiner_model: str = Field(default="gpt-5-nano", env="OPENAI_REFINER_MODEL")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    websocket_port: int = Field(default=8001, env="WEBSOCKET_PORT")
    
    # CORS Configuration
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        env="CORS_ORIGINS"
    )
    
    # Session Configuration
    session_timeout_minutes: int = Field(default=30, env="SESSION_TIMEOUT_MINUTES")
    
    # Redis Configuration (optional)
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def credentials_path(self) -> Path:
        """Get absolute path to GCP credentials file."""
        path = Path(self.google_application_credentials)
        if not path.is_absolute():
            # If relative, assume it's relative to the project root
            return (BASE_DIR / path).resolve()
        return path.resolve()
    
    def validate_gcp_setup(self) -> bool:
        """Check if GCP credentials are properly configured."""
        if not self.gcp_project_id or self.gcp_project_id == "your-project-id-here":
            return False
        
        # Local key file exists
        if self.credentials_path.exists():
            return True
            
        # Fallback: Check if running in Cloud Run (K_SERVICE is set by Cloud Run)
        if os.environ.get("K_SERVICE"):
            return True
            
        return False
    
    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
