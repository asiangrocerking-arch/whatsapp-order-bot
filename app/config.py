"""
配置管理模塊
使用 pydantic 進行環境變量驗證
"""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    # 數據庫配置
    DATABASE_URL: str
    
    # Twilio配置
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_WHATSAPP_NUMBER: str = "whatsapp:+14155238886"
    
    # Cloudinary配置
    CLOUDINARY_URL: Optional[str] = None
    
    # 應用配置
    SECRET_KEY: str
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # API配置
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "WhatsApp訂單機器人"
    
    # CORS配置
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    
    # 安全配置
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8天
    ALGORITHM: str = "HS256"
    
    # 限流配置
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # WhatsApp配置
    WHATSAPP_ORDER_TRIGGERS: list[str] = [
        "我要落單",
        "訂單",
        "order",
        "購買",
        "買"
    ]
    
    # 管理員配置
    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: Optional[str] = None  # 首次運行時需要設置
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    獲取配置單例
    使用 lru_cache 確保只創建一次實例
    """
    return Settings()


# 導出配置實例
settings = get_settings()