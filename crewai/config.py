from pydantic import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ZEPHYR_SCALE_TOKEN: str = os.getenv("ZEPHYR_SCALE_TOKEN", "")
    
    # Zephyr Scale Configuration
    ZEPHYR_API_BASE_URL: str = "https://api.zephyrscale.smartbear.com/v2"
    PROJECT_KEY: str = os.getenv("ZEPHYR_PROJECT_KEY", "QA_DEMO")
    
    # Service URLs
    STORAGE_API_ENDPOINT: str = f"{ZEPHYR_API_BASE_URL}/testcases"
    
    # Agent Configuration
    MAX_TOKENS: int = 150
    TEMPERATURE: float = 0.3
    MODEL_ENGINE: str = "gpt-4"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 