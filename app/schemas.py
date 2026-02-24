"""
Pydantic 數據驗證模式
用於 API 請求和響應
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime


# 商品相關模式
class ProductBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    image_url: Optional[str] = None
    delivery_methods: List[str] = Field(default=["自取"])
    stock: int = Field(default=0, ge=0)
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    image_url: Optional[str] = None
    delivery_methods: Optional[List[str]] = None
    stock: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# 訂單相關模式
class OrderBase(BaseModel):
    customer_whatsapp: str = Field(..., regex=r'^\+[1-9]\d{1,14}$')
    customer_name: Optional[str] = Field(None, max_length=100)
    product_id: int
    quantity: int = Field(default=1, ge=1)
    delivery_method: str
    delivery_location: Optional[str] = None
    delivery_time: Optional[datetime] = None
    admin_notes: Optional[str] = None


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(pending|confirmed|completed|cancelled)$")
    delivery_location: Optional[str] = None
    delivery_time: Optional[datetime] = None
    admin_notes: Optional[str] = None


class Order(OrderBase):
    id: int
    status: str
    total_price: float
    created_at: datetime
    updated_at: datetime
    
    product: Optional[Product] = None

    class Config:
        orm_mode = True


# WhatsApp 會話模式
class WhatsAppSessionBase(BaseModel):
    whatsapp_number: str = Field(..., regex=r'^\+[1-9]\d{1,14}$')
    session_state: str = Field(default="idle")
    session_data: Optional[Dict[str, Any]] = None


class WhatsAppSession(WhatsAppSessionBase):
    id: int
    last_interaction: datetime
    created_at: datetime

    class Config:
        orm_mode = True


# 管理員相關模式
class AdminUserBase(BaseModel):
    username: str = Field(..., max_length=100)
    email: str = Field(..., max_length=200)


class AdminUserCreate(AdminUserBase):
    password: str = Field(..., min_length=8)


class AdminUser(AdminUserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True


# 認證相關模式
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# WhatsApp 消息模式
class WhatsAppMessage(BaseModel):
    from_number: str
    to_number: str
    message_body: str
    message_type: str = "text"
    media_url: Optional[str] = None


# API 響應模式
class MessageResponse(BaseModel):
    message: str


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int