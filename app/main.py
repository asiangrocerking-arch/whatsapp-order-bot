"""
WhatsApp 訂單機器人 - 主應用文件
"""

from datetime import datetime
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware

from . import models
from .database import engine
from .routers import products, orders, whatsapp, admin, auth
from .config import settings
from .middleware import rate_limit_middleware, logging_middleware
from .logger import log

# 創建數據庫表（生產環境應該使用 alembic）
if settings.ENVIRONMENT == "development":
    models.Base.metadata.create_all(bind=engine)

# 創建 FastAPI 應用
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="一個經濟型的 WhatsApp 訂單處理系統",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加中間件
app.add_middleware(BaseHTTPMiddleware, dispatch=rate_limit_middleware)
app.add_middleware(BaseHTTPMiddleware, dispatch=logging_middleware)

# 掛載靜態文件（用於管理界面）
app.mount("/static", StaticFiles(directory="static"), name="static")

# 模板引擎（用於簡單的管理界面）
templates = Jinja2Templates(directory="templates")

# 包含路由
app.include_router(products.router, prefix=settings.API_V1_STR)
app.include_router(orders.router, prefix=settings.API_V1_STR)
app.include_router(whatsapp.router)  # webhook 保持原路徑
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """
    根端點，返回 API 信息
    """
    return {
        "message": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs": "/docs" if settings.DEBUG else None,
        "endpoints": {
            "products": f"{settings.API_V1_STR}/products",
            "orders": f"{settings.API_V1_STR}/orders",
            "whatsapp_webhook": "/webhook/whatsapp",
            "admin": f"{settings.API_V1_STR}/admin"
        }
    }


@app.get("/health")
async def health_check():
    """
    健康檢查端點
    返回服務狀態和版本信息
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


@app.get("/config")
async def get_config():
    """
    獲取當前配置（僅開發環境）
    """
    if settings.ENVIRONMENT == "production":
        raise HTTPException(status_code=403, detail="生產環境不可訪問")
    
    return {
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "database_url": "***" if settings.DATABASE_URL else "Not set",
        "twilio_account_sid": "***" if settings.TWILIO_ACCOUNT_SID else "Not set",
        "cloudinary_url": "***" if settings.CLOUDINARY_URL else "Not set",
    }


# 全局異常處理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局異常處理器
    記錄錯誤並返回友好的錯誤信息
    """
    log.exception(f"Unhandled exception: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "服務器內部錯誤"
        }
    )


# 啟動事件
@app.on_event("startup")
async def startup_event():
    """
    應用啟動時執行的操作
    """
    log.info(f"Starting {settings.PROJECT_NAME}")
    log.info(f"Environment: {settings.ENVIRONMENT}")
    log.info(f"Debug mode: {settings.DEBUG}")


# 關閉事件
@app.on_event("shutdown")
async def shutdown_event():
    """
    應用關閉時執行的操作
    """
    log.info(f"Shutting down {settings.PROJECT_NAME}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=settings.DEBUG
    )