"""
數據模型定義
商品、訂單、客戶等核心模型
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class Product(Base):
    """
    商品模型
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    image_url = Column(String(500), nullable=True)
    # 交收方式存儲為 JSON 數組，如 ["自取", "送貨"]
    delivery_methods = Column(JSON, nullable=False, default=["自取"])
    stock = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 關聯
    orders = relationship("Order", back_populates="product")


class Order(Base):
    """
    訂單模型
    """
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    # WhatsApp 電話號碼（E.164 格式）
    customer_whatsapp = Column(String(20), nullable=False, index=True)
    customer_name = Column(String(100), nullable=True)
    
    # 商品關聯
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    
    # 訂單狀態：pending（待確認）, confirmed（已確認）, completed（已完成）, cancelled（已取消）
    status = Column(String(20), default="pending", nullable=False)
    
    # 交收信息
    delivery_method = Column(String(50), nullable=False)
    delivery_location = Column(String(200), nullable=True)  # 自取地點或送貨地址
    delivery_time = Column(DateTime(timezone=True), nullable=True)
    
    # 訂單總金額
    total_price = Column(Float, nullable=False)
    
    # 管理員備註
    admin_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 關聯
    product = relationship("Product", back_populates="orders")


class WhatsAppSession(Base):
    """
    WhatsApp 會話狀態管理
    追蹤客戶當前的會話狀態
    """
    __tablename__ = "whatsapp_sessions"

    id = Column(Integer, primary_key=True, index=True)
    whatsapp_number = Column(String(20), nullable=False, unique=True, index=True)
    
    # 會話狀態：idle（空閒）, selecting_product（選擇商品中）, confirming_order（確認訂單中）
    session_state = Column(String(30), default="idle")
    
    # 當前會話數據（如臨時選中的商品ID等）
    session_data = Column(JSON, nullable=True)
    
    last_interaction = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AdminUser(Base):
    """
    管理員用戶
    """
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(200), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())