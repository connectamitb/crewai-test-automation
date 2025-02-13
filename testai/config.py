from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    WEAVIATE_URL: str = os.getenv("WEAVIATE_URL")
    WEAVIATE_API_KEY: str = os.getenv("WEAVIATE_API_KEY")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    STORAGE_API_ENDPOINT: str
    ZEPHYR_SCALE_TOKEN: str
    PROJECT_KEY: str = "TEST"  # Default project key for Zephyr Scale

    class Config:
        env_file = ".env"

settings = Settings() 