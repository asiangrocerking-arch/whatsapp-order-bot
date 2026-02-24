"""
WhatsApp 訂單機器人 - 主應用文件
"""

from datetime import datetime
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from dotenv import load_dotenv

from . import models
from .database import engine, get_db
from .routers import products, orders, whatsapp, admin, auth

# 加載環境變量
load_dotenv()

# 創建數據庫表
models.Base.metadata.create_all(bind=engine)

# 創建 FastAPI 應用
app = FastAPI(
    title="WhatsApp 訂單機器人 API",
    description="一個經濟型的 WhatsApp 訂單處理系統",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.getenv("ENVIRONMENT") == "development" else [
        "https://your-frontend-domain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 掛載靜態文件（用於管理界面）
app.mount("/static", StaticFiles(directory="static"), name="static")

# 模板引擎（用於簡單的管理界面）
templates = Jinja2Templates(directory="templates")

# 包含路由
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(whatsapp.router)
app.include_router(auth.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    """
    根端點，返回 API 信息
    """
    return {
        "message": "WhatsApp 訂單機器人 API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "products": "/products",
            "orders": "/orders",
            "whatsapp_webhook": "/webhook/whatsapp",
            "admin": "/admin"
        }
    }


@app.get("/health")
async def health_check():
    """
    健康檢查端點
    """
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/config")
async def get_config():
    """
    獲取當前配置（僅開發環境）
    """
    if os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(status_code=403, detail="生產環境不可訪問")
    
    return {
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database_url": "***" if os.getenv("DATABASE_URL") else "Not set",
        "twilio_account_sid": "***" if os.getenv("TWILIO_ACCOUNT_SID") else "Not set",
        "cloudinary_url": "***" if os.getenv("CLOUDINARY_URL") else "Not set",
    }


# 錯誤處理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development"
    )