"""
商品服务
处理商品相关的业务逻辑
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from fastapi import HTTPException, status

from .. import models, schemas
from ..logger import log


def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False
) -> List[models.Product]:
    """
    获取商品列表
    """
    query = db.query(models.Product)
    if active_only:
        query = query.filter(models.Product.is_active == True)
    return query.offset(skip).limit(limit).all()


def get_product(db: Session, product_id: int) -> Optional[models.Product]:
    """
    根据ID获取商品
    """
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def create_product(db: Session, product: schemas.ProductCreate) -> models.Product:
    """
    创建新商品
    """
    try:
        db_product = models.Product(**product.dict())
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    except SQLAlchemyError as e:
        log.error(f"创建商品失败: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建商品失败"
        )


def update_product(
    db: Session,
    product_id: int,
    product: schemas.ProductUpdate
) -> Optional[models.Product]:
    """
    更新商品信息
    """
    try:
        db_product = get_product(db, product_id)
        if not db_product:
            return None
        
        # 只更新提供的字段
        product_data = product.dict(exclude_unset=True)
        for key, value in product_data.items():
            setattr(db_product, key, value)
        
        db.commit()
        db.refresh(db_product)
        return db_product
        
    except SQLAlchemyError as e:
        log.error(f"更新商品失败: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新商品失败"
        )


def delete_product(db: Session, product_id: int) -> bool:
    """
    删除商品（软删除）
    """
    try:
        db_product = get_product(db, product_id)
        if not db_product:
            return False
        
        # 软删除：设置为非活动状态
        db_product.is_active = False
        db.commit()
        return True
        
    except SQLAlchemyError as e:
        log.error(f"删除商品失败: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除商品失败"
        )


def update_stock(db: Session, product_id: int, quantity_change: int) -> Optional[models.Product]:
    """
    更新商品库存
    """
    try:
        db_product = get_product(db, product_id)
        if not db_product:
            return None
        
        new_stock = db_product.stock + quantity_change
        if new_stock < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="库存不足"
            )
        
        db_product.stock = new_stock
        db.commit()
        db.refresh(db_product)
        return db_product
        
    except SQLAlchemyError as e:
        log.error(f"更新库存失败: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新库存失败"
        )