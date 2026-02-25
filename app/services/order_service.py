"""
订单服务
处理订单相关的业务逻辑
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from fastapi import HTTPException, status
from datetime import datetime

from .. import models, schemas
from ..logger import log
from . import product_service


def get_orders(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    customer_whatsapp: Optional[str] = None
) -> List[models.Order]:
    """
    获取订单列表
    可以按客户筛选
    """
    query = db.query(models.Order)
    if customer_whatsapp:
        query = query.filter(models.Order.customer_whatsapp == customer_whatsapp)
    return query.order_by(models.Order.created_at.desc()).offset(skip).limit(limit).all()


def get_order(db: Session, order_id: int) -> Optional[models.Order]:
    """
    根据ID获取订单
    """
    return db.query(models.Order).filter(models.Order.id == order_id).first()


def create_order(db: Session, order: schemas.OrderCreate) -> models.Order:
    """
    创建新订单
    """
    try:
        # 检查商品是否存在且有库存
        product = product_service.get_product(db, order.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="商品不存在"
            )
        
        if product.stock < order.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="商品库存不足"
            )
        
        # 创建订单
        total_price = product.price * order.quantity
        db_order = models.Order(
            **order.dict(),
            total_price=total_price,
            status="pending"
        )
        
        # 更新库存
        product.stock -= order.quantity
        
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        return db_order
        
    except SQLAlchemyError as e:
        log.error(f"创建订单失败: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建订单失败"
        )


def update_order_status(
    db: Session,
    order_id: int,
    status: str,
    admin_notes: Optional[str] = None
) -> Optional[models.Order]:
    """
    更新订单状态
    """
    try:
        db_order = get_order(db, order_id)
        if not db_order:
            return None
        
        # 验证状态转换是否合法
        valid_transitions = {
            "pending": ["confirmed", "cancelled"],
            "confirmed": ["completed", "cancelled"],
            "completed": [],
            "cancelled": []
        }
        
        if status not in valid_transitions.get(db_order.status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的状态转换"
            )
        
        # 更新状态
        db_order.status = status
        if admin_notes:
            db_order.admin_notes = admin_notes
        
        # 如果取消订单，恢复库存
        if status == "cancelled" and db_order.status != "cancelled":
            product = product_service.get_product(db, db_order.product_id)
            if product:
                product.stock += db_order.quantity
        
        db.commit()
        db.refresh(db_order)
        return db_order
        
    except SQLAlchemyError as e:
        log.error(f"更新订单状态失败: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新订单状态失败"
        )


def update_order_delivery(
    db: Session,
    order_id: int,
    delivery_location: Optional[str] = None,
    delivery_time: Optional[datetime] = None
) -> Optional[models.Order]:
    """
    更新订单配送信息
    """
    try:
        db_order = get_order(db, order_id)
        if not db_order:
            return None
        
        if delivery_location:
            db_order.delivery_location = delivery_location
        if delivery_time:
            db_order.delivery_time = delivery_time
            
        db.commit()
        db.refresh(db_order)
        return db_order
        
    except SQLAlchemyError as e:
        log.error(f"更新订单配送信息失败: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新订单配送信息失败"
        )