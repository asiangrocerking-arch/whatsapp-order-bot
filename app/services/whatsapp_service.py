"""
WhatsApp 消息處理服務
使用 Twilio WhatsApp API
"""

import os
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from .. import models, schemas
from ..database import get_db

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Twilio 客戶端
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")  # Sandbox number

client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
else:
    logger.warning("Twilio credentials not set. WhatsApp functionality will be limited.")


class WhatsAppService:
    """
    WhatsApp 消息處理服務
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def send_message(self, to_number: str, message: str, media_url: Optional[str] = None):
        """
        發送 WhatsApp 消息
        """
        if not client:
            logger.error("Twilio client not initialized")
            return False
        
        try:
            message_params = {
                "from": TWILIO_WHATSAPP_NUMBER,
                "to": f"whatsapp:{to_number}",
                "body": message
            }
            
            if media_url:
                message_params["media_url"] = media_url
            
            message = client.messages.create(**message_params)
            logger.info(f"WhatsApp message sent to {to_number}: {message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return False
    
    def handle_incoming_message(self, from_number: str, message_body: str, is_group: bool = False):
        """
        處理收到的 WhatsApp 消息
        """
        # 清理電話號碼格式
        from_number = self._clean_phone_number(from_number)
        
        # 如果是群組消息，檢查是否有訂單觸發關鍵詞
        if is_group:
            return self._handle_group_message(from_number, message_body)
        
        # 私訊：處理會話狀態
        return self._handle_private_message(from_number, message_body)
    
    def _handle_group_message(self, from_number: str, message_body: str):
        """
        處理群組消息
        """
        # 檢查是否包含訂單觸發關鍵詞
        trigger_keywords = ["我要落單", "訂單", "order", "購買", "買"]
        
        for keyword in trigger_keywords:
            if keyword in message_body:
                logger.info(f"Order trigger detected from {from_number} in group")
                
                # 獲取或創建會話
                session = self._get_or_create_session(from_number)
                
                # 發送私訊給客戶
                self._send_welcome_message(from_number)
                
                # 更新會話狀態
                session.session_state = "selecting_product"
                session.last_interaction = datetime.now()
                self.db.commit()
                
                return {
                    "action": "triggered_private_message",
                    "customer": from_number
                }
        
        # 非觸發消息，忽略
        return {"action": "ignored"}
    
    def _handle_private_message(self, from_number: str, message_body: str):
        """
        處理私訊
        """
        # 獲取或創建會話
        session = self._get_or_create_session(from_number)
        
        # 根據會話狀態處理消息
        if session.session_state == "selecting_product":
            return self._handle_product_selection(session, message_body)
        elif session.session_state == "confirming_order":
            return self._handle_order_confirmation(session, message_body)
        else:
            # 默認：發送歡迎消息和商品列表
            return self._send_product_list(from_number, session)
    
    def _send_welcome_message(self, to_number: str):
        """
        發送歡迎消息
        """
        welcome_msg = """您好！歡迎使用訂單服務。我將在私訊中為您處理訂單。

請稍候，我將為您列出可選商品..."""
        
        self.send_message(to_number, welcome_msg)
    
    def _send_product_list(self, to_number: str, session: models.WhatsAppSession):
        """
        發送商品列表
        """
        # 獲取所有啟用中的商品
        products = self.db.query(models.Product).filter(
            models.Product.is_active == True,
            models.Product.stock > 0
        ).order_by(models.Product.name).all()
        
        if not products:
            self.send_message(to_number, "目前沒有可選商品，請稍後再試。")
            return {"action": "no_products"}
        
        # 構建商品列表消息
        product_list = "請選擇商品（回覆數字）：\n\n"
        for i, product in enumerate(products, 1):
            delivery_methods = "/".join(product.delivery_methods)
            product_list += f"{i}. {product.name} - ${product.price} ({delivery_methods})\n"
            if product.description:
                product_list += f"   {product.description[:50]}...\n"
        
        product_list += "\n回覆數字選擇商品，或輸入「取消」退出。"
        
        self.send_message(to_number, product_list)
        
        # 保存商品列表到會話
        session.session_state = "selecting_product"
        session.session_data = {
            "product_list": [p.id for p in products],
            "step": "product_selection"
        }
        session.last_interaction = datetime.now()
        self.db.commit()
        
        return {"action": "sent_product_list", "product_count": len(products)}
    
    def _handle_product_selection(self, session: models.WhatsAppSession, message: str):
        """
        處理商品選擇
        """
        # 檢查是否取消
        if message.lower() in ["取消", "cancel", "退出", "exit"]:
            self.send_message(session.whatsapp_number, "訂單已取消。如有需要，請隨時再次聯繫。")
            session.session_state = "idle"
            session.session_data = None
            self.db.commit()
            return {"action": "cancelled"}
        
        # 嘗試解析選擇的數字
        try:
            choice = int(message.strip())
            product_list = session.session_data.get("product_list", [])
            
            if choice < 1 or choice > len(product_list):
                raise ValueError("選擇無效")
            
            product_id = product_list[choice - 1]
            product = self.db.query(models.Product).filter(models.Product.id == product_id).first()
            
            if not product or not product.is_active or product.stock <= 0:
                self.send_message(session.whatsapp_number, "該商品暫時無法購買，請選擇其他商品。")
                return {"action": "product_unavailable"}
            
            # 詢問數量
            quantity_msg = f"您選擇了：{product.name}\n價格：${product.price}\n\n請輸入購買數量（1-{min(product.stock, 10)}）："
            self.send_message(session.whatsapp_number, quantity_msg)
            
            # 更新會話
            session.session_state = "confirming_order"
            session.session_data = {
                "selected_product_id": product_id,
                "step": "quantity_selection"
            }
            self.db.commit()
            
            return {
                "action": "product_selected",
                "product_id": product_id,
                "product_name": product.name
            }
            
        except (ValueError, IndexError):
            # 無效選擇
            self.send_message(session.whatsapp_number, "請輸入有效的數字選擇商品。")
            return {"action": "invalid_selection"}
    
    def _handle_order_confirmation(self, session: models.WhatsAppSession, message: str):
        """
        處理訂單確認
        """
        try:
            # 獲取選中的商品
            product_id = session.session_data.get("selected_product_id")
            product = self.db.query(models.Product).filter(models.Product.id == product_id).first()
            
            if not product:
                self.send_message(session.whatsapp_number, "商品不存在，請重新開始。")
                session.session_state = "idle"
                session.session_data = None
                self.db.commit()
                return {"action": "product_not_found"}
            
            # 處理數量輸入
            if session.session_data.get("step") == "quantity_selection":
                try:
                    quantity = int(message.strip())
                    if quantity < 1 or quantity > product.stock:
                        self.send_message(
                            session.whatsapp_number, 
                            f"請輸入有效數量（1-{product.stock}）。"
                        )
                        return {"action": "invalid_quantity"}
                    
                    # 詢問交收方式
                    delivery_options = "/".join(product.delivery_methods)
                    delivery_msg = f"數量：{quantity}\n總價：${product.price * quantity}\n\n請選擇交收方式（{delivery_options}）："
                    self.send_message(session.whatsapp_number, delivery_msg)
                    
                    # 更新會話
                    session.session_data.update({
                        "quantity": quantity,
                        "step": "delivery_selection"
                    })
                    self.db.commit()
                    
                    return {"action": "quantity_set", "quantity": quantity}
                    
                except ValueError:
                    self.send_message(session.whatsapp_number, "請輸入有效的數字。")
                    return {"action": "invalid_input"}
            
            # 處理交收方式選擇
            elif session.session_data.get("step") == "delivery_selection":
                delivery_method = message.strip()
                
                if delivery_method not in product.delivery_methods:
                    self.send_message(
                        session.whatsapp_number,
                        f"請輸入有效的交收方式：{', '.join(product.delivery_methods)}"
                    )
                    return {"action": "invalid_delivery_method"}
                
                # 創建訂單
                order = models.Order(
                    customer_whatsapp=session.whatsapp_number,
                    product_id=product.id,
                    quantity=session.session_data["quantity"],
                    delivery_method=delivery_method,
                    total_price=product.price * session.session_data["quantity"],
                    status="pending"
                )
                
                # 更新庫存
                product.stock -= session.session_data["quantity"]
                
                self.db.add(order)
                self.db.commit()
                self.db.refresh(order)
                
                # 發送訂單確認
                confirmation_msg = f"""✅ 訂單已確認！

商品：{product.name}
數量：{session.session_data['quantity']}
總價：${order.total_price}
交收方式：{delivery_method}
訂單編號：{order.id}

管理員將稍後與您確認交收細節。
感謝您的訂購！"""
                
                self.send_message(session.whatsapp_number, confirmation_msg)
                
                # 重置會話
                session.session_state = "idle"
                session.session_data = None
                self.db.commit()
                
                # TODO: 通知管理員
                
                return {
                    "action": "order_created",
                    "order_id": order.id,
                    "customer": session.whatsapp_number
                }
        
        except Exception as e:
            logger.error(f"Error in order confirmation: {e}")
            self.send_message(session.whatsapp_number, "處理訂單時發生錯誤，請重新開始。")
            session.session_state = "idle"
            session.session_data = None
            self.db.commit()
            return {"action": "error", "error": str(e)}
    
    def _get_or_create_session(self, whatsapp_number: str) -> models.WhatsAppSession:
        """
        獲取或創建 WhatsApp 會話
        """
        session = self.db.query(models.WhatsAppSession).filter(
            models.WhatsAppSession.whatsapp_number == whatsapp_number
        ).first()
        
        if not session:
            session = models.WhatsAppSession(
                whatsapp_number=whatsapp_number,
                session_state="idle"
            )
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
        
        return session
    
    def _clean_phone_number(self, phone_number: str) -> str:
        """
        清理電話號碼格式
        """
        # 移除 "whatsapp:" 前綴
        if phone_number.startswith("whatsapp:"):
            phone_number = phone_number[9:]
        
        # 確保以 + 開頭
        if not phone_number.startswith("+"):
            # 假設是香港號碼
            if phone_number.startswith("852"):
                phone_number = "+" + phone_number
            else:
                phone_number = "+852" + phone_number.lstrip("0")
        
        return phone_number
    
    def send_order_confirmation(self, order: models.Order):
        """
        發送訂單確認給客戶（管理員確認後）
        """
        product = order.product
        message = f"""您的訂單 #{order.id} 已確認！

商品：{product.name}
數量：{order.quantity}
總價：${order.total_price}
交收方式：{order.delivery_method}
{f'交收地點：{order.delivery_location}' if order.delivery_location else ''}
{f'交收時間：{order.delivery_time}' if order.delivery_time else ''}

如有問題，請聯繫我們。
感謝您的訂購！"""
        
        return self.send_message(order.customer_whatsapp, message)
    
    def send_order_status_update(self, order: models.Order):
        """
        發送訂單狀態更新給客戶
        """
        status_messages = {
            "confirmed": "您的訂單已確認，正在安排交收。",
            "completed": "您的訂單已完成，感謝您的惠顧！",
            "cancelled": "您的訂單已取消。"
        }
        
        if order.status in status_messages:
            message = f"訂單 #{order.id} 狀態更新：{status_messages[order.status]}"
            if order.admin_notes:
                message += f"\n備註：{order.admin_notes}"
            
            return self.send_message(order.customer_whatsapp, message)
        
        return False