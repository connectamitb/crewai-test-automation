from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    OPENAI_API_KEY: str
    STORAGE_API_ENDPOINT: str
    LOG_LEVEL: str = "INFO"
    ZEPHYR_SCALE_TOKEN: str
    PROJECT_KEY: str = "TEST"  # Default project key for Zephyr Scale

    class Config:
        env_file = ".env"

settings = Settings() 