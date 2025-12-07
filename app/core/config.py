from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Antony HFT"
    API_V1_STR: str = "/api/v1"
    
    # Upstox API
    UPSTOX_API_KEY: str
    UPSTOX_API_SECRET: str
    UPSTOX_REDIRECT_URI: str
    UPSTOX_ACCESS_TOKEN: str = ""
    
    # Sandbox Mode - Real money இல்லாம testing
    UPSTOX_SANDBOX_MODE: bool = False
    UPSTOX_SANDBOX_TOKEN: str = ""
    
    # Redis
    REDIS_URL: str
    
    # PostgreSQL
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: str
    POSTGRES_DB: str
    
    @property
    def active_token(self) -> str:
        """Get active token based on mode"""
        if self.UPSTOX_SANDBOX_MODE:
            return self.UPSTOX_SANDBOX_TOKEN
        return self.UPSTOX_ACCESS_TOKEN
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()

