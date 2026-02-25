"""
服务模块初始化
"""

from . import product_service
from . import order_service
from . import whatsapp_service

# 导出服务
__all__ = ['product_service', 'order_service', 'whatsapp_service']