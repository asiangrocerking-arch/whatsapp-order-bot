"""
數據庫配置
使用 SQLAlchemy ORM 連接 PostgreSQL
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# 加載環境變量
load_dotenv()

def get_database_url():
    """
    獲取數據庫 URL 並處理 Render.com 的 PostgreSQL URL 格式
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return "sqlite:///./test.db"
    
    # Render.com 提供的 PostgreSQL URL 以 "postgres://" 開頭
    # SQLAlchemy 2.0+ 需要 "postgresql://"
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    return database_url

# 數據庫連接 URL
DATABASE_URL = get_database_url()

# 創建引擎時添加連接池配置
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=2,
    pool_timeout=30,
    pool_recycle=1800,  # 30分鐘
    connect_args={
        "connect_timeout": 10,  # 連接超時10秒
        **({"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 依賴項：獲取數據庫會話
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()