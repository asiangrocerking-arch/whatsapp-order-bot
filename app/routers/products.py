"""
商品管理 API 路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import schemas, models
from ..database import get_db
from ..services import product_service

router = APIRouter(
    prefix="/products",
    tags=["products"]
)


@router.get("/", response_model=List[schemas.Product])
def get_products(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True, description="只返回啟用中的商品"),
    search: Optional[str] = Query(None, description="商品名稱搜索")
):
    """
    獲取商品列表
    """
    query = db.query(models.Product)
    
    if active_only:
        query = query.filter(models.Product.is_active == True)
    
    if search:
        query = query.filter(models.Product.name.ilike(f"%{search}%"))
    
    products = query.order_by(models.Product.created_at.desc()).offset(skip).limit(limit).all()
    return products


@router.get("/{product_id}", response_model=schemas.Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    獲取單個商品詳細信息
    """
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    return product


@router.post("/", response_model=schemas.Product, status_code=status.HTTP_201_CREATED)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    """
    創建新商品（管理員功能）
    """
    # 檢查商品名稱是否已存在
    existing = db.query(models.Product).filter(
        models.Product.name == product.name
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="商品名稱已存在"
        )
    
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.put("/{product_id}", response_model=schemas.Product)
def update_product(
    product_id: int, 
    product_update: schemas.ProductUpdate, 
    db: Session = Depends(get_db)
):
    """
    更新商品信息（管理員功能）
    """
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    
    # 更新字段
    update_data = product_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product


@router.delete("/{product_id}", response_model=schemas.MessageResponse)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """
    刪除商品（實際上是軟刪除，設置為不啟用）
    """
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品不存在"
        )
    
    db_product.is_active = False
    db.commit()
    
    return {"message": "商品已停用"}


@router.get("/active/list", response_model=List[schemas.Product])
def get_active_products(db: Session = Depends(get_db)):
    """
    獲取所有啟用中的商品列表（WhatsApp 機器人用）
    """
    products = db.query(models.Product).filter(
        models.Product.is_active == True,
        models.Product.stock > 0
    ).order_by(models.Product.name).all()
    return products