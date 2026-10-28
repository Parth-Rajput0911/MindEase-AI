"""
Application configuration for MindEase-AI backend.
Supports environment variables and .env file loading.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base backend directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env file if it exists
load_dotenv(BASE_DIR / ".env")


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "MindEase-AI")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

    # Database configuration - defaults to SQLite in the Backend directory
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'mindease.db'}"
    )

    API_V1_PREFIX: str = os.getenv("API_V1_PREFIX", "/api/v1")


settings = Settings()
