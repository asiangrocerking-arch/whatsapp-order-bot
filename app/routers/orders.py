"""
訂單管理 API 路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from .. import schemas, models
from ..database import get_db
from ..services import order_service, whatsapp_service

router = APIRouter(
    prefix="/orders",
    tags=["orders"]
)


@router.get("/", response_model=List[schemas.Order])
def get_orders(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="訂單狀態篩選"),
    customer_whatsapp: Optional[str] = Query(None, description="客戶 WhatsApp 號碼篩選"),
    start_date: Optional[datetime] = Query(None, description="開始日期"),
    end_date: Optional[datetime] = Query(None, description="結束日期")
):
    """
    獲取訂單列表（管理員功能）
    """
    query = db.query(models.Order).join(models.Product)
    
    if status:
        query = query.filter(models.Order.status == status)
    
    if customer_whatsapp:
        query = query.filter(models.Order.customer_whatsapp == customer_whatsapp)
    
    if start_date:
        query = query.filter(models.Order.created_at >= start_date)
    
    if end_date:
        query = query.filter(models.Order.created_at <= end_date)
    
    orders = query.order_by(models.Order.created_at.desc()).offset(skip).limit(limit).all()
    return orders


@router.get("/{order_id}", response_model=schemas.Order)
def get_order(order_id: int, db: Session = Depends(get_db)):
    """
    獲取單個訂單詳細信息
    """
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="訂單不存在"
        )
    return order


@router.post("/", response_model=schemas.Order, status_code=status.HTTP_201_CREATED)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    """
    創建新訂單（WhatsApp 機器人用）
    """
    # 檢查商品是否存在且有庫存
    product = db.query(models.Product).filter(
        models.Product.id == order.product_id,
        models.Product.is_active == True
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="商品不存在或已停用"
        )
    
    if product.stock < order.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"庫存不足，僅剩 {product.stock} 件"
        )
    
    # 檢查交收方式是否有效
    if order.delivery_method not in product.delivery_methods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"無效的交收方式，可選：{', '.join(product.delivery_methods)}"
        )
    
    # 計算總金額
    total_price = product.price * order.quantity
    
    # 創建訂單
    db_order = models.Order(
        **order.dict(),
        total_price=total_price,
        status="pending"
    )
    
    # 更新庫存
    product.stock -= order.quantity
    
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # TODO: 發送 WhatsApp 確認消息給客戶
    # whatsapp_service.send_order_confirmation(db_order)
    
    # TODO: 通知管理員有新訂單
    # notify_admin_new_order(db_order)
    
    return db_order


@router.put("/{order_id}", response_model=schemas.Order)
def update_order(
    order_id: int, 
    order_update: schemas.OrderUpdate, 
    db: Session = Depends(get_db)
):
    """
    更新訂單信息（管理員功能）
    """
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="訂單不存在"
        )
    
    # 更新字段
    update_data = order_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_order, field, value)
    
    db.commit()
    db.refresh(db_order)
    
    # 如果狀態變更，通知客戶
    if "status" in update_data:
        # TODO: 發送狀態更新通知給客戶
        # whatsapp_service.send_status_update(db_order)
        pass
    
    return db_order


@router.get("/today/summary")
def get_today_summary(db: Session = Depends(get_db)):
    """
    獲取今日訂單摘要（管理員儀表板用）
    """
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    # 今日訂單數
    total_orders = db.query(models.Order).filter(
        models.Order.created_at >= today_start,
        models.Order.created_at < today_end
    ).count()
    
    # 今日銷售額
    total_sales = db.query(models.Order).filter(
        models.Order.created_at >= today_start,
        models.Order.created_at < today_end,
        models.Order.status.in_(["confirmed", "completed"])
    ).with_entities(func.sum(models.Order.total_price)).scalar() or 0
    
    # 待處理訂單
    pending_orders = db.query(models.Order).filter(
        models.Order.status == "pending"
    ).count()
    
    return {
        "date": today_start.date().isoformat(),
        "total_orders": total_orders,
        "total_sales": total_sales,
        "pending_orders": pending_orders
    }


@router.get("/customer/{whatsapp_number}", response_model=List[schemas.Order])
def get_customer_orders(
    whatsapp_number: str,
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=100)
):
    """
    獲取指定客戶的訂單歷史
    """
    orders = db.query(models.Order).filter(
        models.Order.customer_whatsapp == whatsapp_number
    ).order_by(models.Order.created_at.desc()).limit(limit).all()
    
    return orders


@router.post("/{order_id}/confirm", response_model=schemas.Order)
def confirm_order(order_id: int, db: Session = Depends(get_db)):
    """
    確認訂單（管理員操作）
    """
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="訂單不存在"
        )
    
    if order.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"訂單狀態為 {order.status}，無法確認"
        )
    
    order.status = "confirmed"
    db.commit()
    db.refresh(order)
    
    # TODO: 發送確認通知給客戶
    # whatsapp_service.send_order_confirmed(order)
    
    return order


@router.post("/{order_id}/complete", response_model=schemas.Order)
def complete_order(order_id: int, db: Session = Depends(get_db)):
    """
    標記訂單為已完成（管理員操作）
    """
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="訂單不存在"
        )
    
    if order.status != "confirmed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"訂單狀態為 {order.status}，無法標記為完成"
        )
    
    order.status = "completed"
    db.commit()
    db.refresh(order)
    
    # TODO: 發送完成通知給客戶
    # whatsapp_service.send_order_completed(order)
    
    return order