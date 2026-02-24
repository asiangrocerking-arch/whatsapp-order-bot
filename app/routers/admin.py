"""
管理員 API 路由
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..database import get_db
from .. import schemas, models
from .auth import verify_token

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

security = HTTPBearer()


@router.get("/dashboard")
async def admin_dashboard(
    payload: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    管理員儀表板數據
    """
    # 基本統計
    total_products = db.query(models.Product).count()
    total_orders = db.query(models.Order).count()
    total_customers = db.query(models.Order.customer_whatsapp).distinct().count()
    
    # 訂單狀態統計
    pending_orders = db.query(models.Order).filter(models.Order.status == "pending").count()
    confirmed_orders = db.query(models.Order).filter(models.Order.status == "confirmed").count()
    completed_orders = db.query(models.Order).filter(models.Order.status == "completed").count()
    
    # 銷售統計（今日）
    from datetime import datetime, timedelta
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    today_sales = db.query(models.Order).filter(
        models.Order.created_at >= today_start,
        models.Order.created_at < today_end,
        models.Order.status.in_(["confirmed", "completed"])
    ).with_entities(func.sum(models.Order.total_price)).scalar() or 0
    
    # 低庫存商品
    low_stock_products = db.query(models.Product).filter(
        models.Product.stock < 10,
        models.Product.is_active == True
    ).order_by(models.Product.stock).limit(10).all()
    
    return {
        "summary": {
            "total_products": total_products,
            "total_orders": total_orders,
            "total_customers": total_customers,
            "today_sales": today_sales
        },
        "order_status": {
            "pending": pending_orders,
            "confirmed": confirmed_orders,
            "completed": completed_orders
        },
        "low_stock_products": [
            {
                "id": p.id,
                "name": p.name,
                "stock": p.stock,
                "price": p.price
            }
            for p in low_stock_products
        ]
    }


@router.get("/recent-orders")
async def get_recent_orders(
    payload: dict = Depends(verify_token),
    db: Session = Depends(get_db),
    limit: int = 10
):
    """
    獲取最近訂單
    """
    orders = db.query(models.Order).join(models.Product).order_by(
        models.Order.created_at.desc()
    ).limit(limit).all()
    
    return [
        {
            "id": order.id,
            "customer_whatsapp": order.customer_whatsapp,
            "customer_name": order.customer_name,
            "product_name": order.product.name,
            "quantity": order.quantity,
            "total_price": order.total_price,
            "status": order.status,
            "created_at": order.created_at,
            "delivery_method": order.delivery_method
        }
        for order in orders
    ]


@router.post("/broadcast")
async def broadcast_message(
    broadcast_data: Dict[str, Any],
    payload: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    廣播消息給所有客戶（謹慎使用）
    """
    message = broadcast_data.get("message")
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message is required"
        )
    
    # 獲取所有客戶
    customers = db.query(models.Order.customer_whatsapp).distinct().all()
    
    # 統計
    return {
        "message": "Broadcast initiated",
        "customer_count": len(customers),
        "message_preview": message[:100] + ("..." if len(message) > 100 else "")
    }


@router.get("/system-status")
async def system_status(
    payload: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    系統狀態檢查
    """
    import os
    
    # 數據庫連接測試
    db_ok = False
    try:
        db.execute("SELECT 1")
        db_ok = True
    except:
        pass
    
    # Twilio 配置檢查
    twilio_configured = bool(os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN"))
    
    # Cloudinary 配置檢查
    cloudinary_configured = bool(os.getenv("CLOUDINARY_URL"))
    
    # 應用信息
    from .. import __version__
    
    return {
        "status": {
            "database": "connected" if db_ok else "disconnected",
            "twilio": "configured" if twilio_configured else "not configured",
            "cloudinary": "configured" if cloudinary_configured else "not configured",
            "environment": os.getenv("ENVIRONMENT", "development")
        },
        "version": __version__,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/reset-test-data")
async def reset_test_data(
    payload: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    重置測試數據（僅開發環境）
    """
    import os
    
    if os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed in production"
        )
    
    # 刪除所有測試數據
    db.query(models.Order).delete()
    db.query(models.WhatsAppSession).delete()
    
    # 重置商品庫存
    products = db.query(models.Product).all()
    for product in products:
        product.stock = 100
    
    db.commit()
    
    return {"message": "Test data reset successfully"}