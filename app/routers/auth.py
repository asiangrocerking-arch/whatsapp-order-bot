"""
認證 API 路由
簡化版本，使用固定管理員帳號
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import os
from datetime import datetime, timedelta
import jwt

from ..database import get_db
from .. import schemas, models

router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

security = HTTPBearer()

# 固定管理員帳號（首次啟動時創建）
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict):
    """
    創建 JWT 訪問令牌
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    驗證 JWT 令牌
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/login", response_model=schemas.Token)
async def login(login_data: schemas.AdminUserCreate):
    """
    管理員登錄
    """
    # 檢查用戶名和密碼
    if (login_data.username != ADMIN_USERNAME or 
        login_data.password != ADMIN_PASSWORD):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 創建訪問令牌
    access_token = create_access_token(data={"sub": login_data.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
async def get_current_user(payload: dict = Depends(verify_token)):
    """
    獲取當前用戶信息
    """
    return {
        "username": payload.get("sub"),
        "is_admin": True
    }


@router.post("/init-admin")
async def initialize_admin(db: Session = Depends(get_db)):
    """
    初始化管理員帳號（首次運行時調用）
    """
    # 檢查是否已有管理員
    existing_admin = db.query(models.AdminUser).filter(
        models.AdminUser.username == ADMIN_USERNAME
    ).first()
    
    if existing_admin:
        return {"message": "Admin user already exists"}
    
    # 創建管理員用戶
    admin_user = models.AdminUser(
        username=ADMIN_USERNAME,
        email=os.getenv("ADMIN_EMAIL", "admin@example.com"),
        hashed_password="hashed_password_placeholder",  # 實際項目中應使用密碼哈希
        is_active=True
    )
    
    db.add(admin_user)
    db.commit()
    
    return {
        "message": "Admin user created",
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD,
        "note": "Please change the password in production!"
    }


@router.get("/protected-test")
async def protected_endpoint(payload: dict = Depends(verify_token)):
    """
    受保護的端點測試
    """
    return {
        "message": "You have access to protected content",
        "user": payload.get("sub")
    }