import os
from pydantic_settings import BaseSettings
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Developer Landing API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    # OpenAI
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    MISTRAL_MODEL: str = os.getenv("MISTRAL_MODEL", "mistral-small-latest")

    @property
    def mistral_available(self) -> bool:
        """Check if Mistral AI is configured"""
        return bool(self.MISTRAL_API_KEY)

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "")
    SMTP_TO: str = os.getenv("SMTP_TO", "")

    # Rate Limiting
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour
    RATE_LIMIT_MAX_REQUESTS: int = 5

    # File Storage
    DATA_DIR: str = "data"
    LOGS_DIR: str = "data/logs"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
