from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # GitHub Configuration
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    github_webhook_secret: Optional[str] = os.getenv("GITHUB_WEBHOOK_SECRET")
    github_app_id: Optional[str] = os.getenv("GITHUB_APP_ID")
    github_app_private_key: Optional[str] = os.getenv("GITHUB_APP_PRIVATE_KEY")
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    openai_temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    
    # Application Configuration
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # Security Review Configuration
    checkov_skip_checks: list = []
    min_severity_level: str = os.getenv("MIN_SEVERITY_LEVEL", "LOW")
    auto_fix_enabled: bool = os.getenv("AUTO_FIX_ENABLED", "True").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = True 