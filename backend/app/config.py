"""Configuration settings for the application."""
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql://localhost:5432/crypto_manager"
    
    # Binance API
    binance_api_key: str = ""
    binance_api_secret: str = ""
    binance_testnet: bool = False
    
    # Telegram Configuration
    telegram_api_id: int = 0
    telegram_api_hash: str = ""
    telegram_session_string: str = ""
    telegram_group_id: int = 0
    
    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    
    # Default Trade Settings
    default_leverage: int = 20
    default_position_size: float = 50.0
    default_sl_percentage: float = 5.0
    default_tp_percentage: float = 2.5
    default_margin_mode: str = "CROSSED"
    default_max_concurrent: int = 5
    auto_execute_trades: bool = True
    
    # User Configuration
    default_user_id: int = 1
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
