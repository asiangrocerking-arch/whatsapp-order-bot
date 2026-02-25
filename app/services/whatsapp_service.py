"""
WhatsApp 服务
处理 WhatsApp 消息和会话管理
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, status
import os
from datetime import datetime
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from .. import models, schemas
from ..logger import log
from . import product_service, order_service

# Twilio 配置
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")


class WhatsAppService:
    """
    WhatsApp 消息处理服务
    """
    def __init__(self, db: Session):
        """
        初始化服务
        """
        self.db = db
        self.client = None
        if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
            self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        else:
            log.warning("Twilio credentials not set")

    def send_message(
        self,
        to_number: str,
        message: str,
        media_url: Optional[str] = None
    ) -> bool:
        """发送 WhatsApp 消息"""
        if not self.client:
            log.error("Twilio client not initialized")
            return False

        try:
            # 确保号码格式正确
            if not to_number.startswith("whatsapp:"):
                to_number = f"whatsapp:{to_number}"

            # 准备消息参数
            message_params = {
                "from_": TWILIO_WHATSAPP_NUMBER,
                "to": to_number,
                "body": message
            }

            if media_url:
                message_params["media_url"] = [media_url]

            # 发送消息
            message = self.client.messages.create(**message_params)
            log.info(f"WhatsApp message sent to {to_number}: {message.sid}")
            return True

        except TwilioRestException as e:
            log.error(f"Twilio error: {str(e)}")
            return False
        except Exception as e:
            log.error(f"Error sending WhatsApp message: {str(e)}")
            return False

    def handle_incoming_message(
        self,
        from_number: str,
        message_body: str,
        is_group: bool = False
    ) -> Dict[str, Any]:
        """处理收到的 WhatsApp 消息"""
        try:
            # 清理号码格式
            if from_number.startswith("whatsapp:"):
                from_number = from_number[9:]

            # 如果是群组消息，检查触发关键词
            if is_group:
                return self._handle_group_message(from_number, message_body)

            # 获取或创建会话
            session = self._get_or_create_session(from_number)

            # 根据会话状态处理消息
            if session.session_state == "selecting_product":
                return self._handle_product_selection(session, message_body)
            elif session.session_state == "entering_quantity":
                return self._handle_quantity_input(session, message_body)
            elif session.session_state == "selecting_delivery":
                return self._handle_delivery_selection(session, message_body)
            else:
                # 默认：发送商品列表
                return self._send_product_list(session)

        except Exception as e:
            log.error(f"Error handling WhatsApp message: {str(e)}")
            # 发送错误消息
            self.send_message(from_number, "抱歉，处理您的消息时出现错误。请稍后再试。")
            return {"action": "error", "error": str(e)}

    def _get_or_create_session(self, whatsapp_number: str) -> models.WhatsAppSession:
        """获取或创建 WhatsApp 会话"""
        try:
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

        except SQLAlchemyError as e:
            log.error(f"Database error in get_or_create_session: {str(e)}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="会话创建失败"
            )

    def _update_session_state(
        self,
        session: models.WhatsAppSession,
        new_state: str,
        session_data: Optional[Dict[str, Any]] = None
    ) -> models.WhatsAppSession:
        """更新会话状态"""
        try:
            session.session_state = new_state
            if session_data is not None:
                session.session_data = session_data
            session.last_interaction = datetime.now()
            
            self.db.commit()
            self.db.refresh(session)
            return session
            
        except SQLAlchemyError as e:
            log.error(f"Database error in update_session_state: {str(e)}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="会话更新失败"
            )

    def _handle_group_message(
        self,
        from_number: str,
        message_body: str
    ) -> Dict[str, Any]:
        """处理群组消息"""
        # 检查触发关键词
        triggers = ["我要落单", "訂單", "order", "購買", "買"]
        if any(trigger in message_body.lower() for trigger in triggers):
            # 发送私聊引导消息
            welcome_msg = """您好！我将在私聊中为您处理订单。
请稍等，我会发送商品列表给您..."""
            
            if self.send_message(from_number, welcome_msg):
                session = self._get_or_create_session(from_number)
                return self._send_product_list(session)
            
        return {"action": "ignored"}

    def _send_product_list(
        self,
        session: models.WhatsAppSession
    ) -> Dict[str, Any]:
        """发送商品列表"""
        # 获取可用商品
        products = self.db.query(models.Product).filter(
            models.Product.is_active == True,
            models.Product.stock > 0
        ).all()

        if not products:
            self.send_message(
                session.whatsapp_number,
                "抱歉，目前没有可用商品。请稍后再试。"
            )
            return {"action": "no_products"}

        # 构建商品列表消息
        product_list = "请选择商品（回复数字）：\n\n"
        for i, product in enumerate(products, 1):
            delivery_methods = "/".join(product.delivery_methods)
            product_list += f"{i}. {product.name} - ${product.price}\n"
            product_list += f"   库存: {product.stock} | 配送: {delivery_methods}\n"
            if product.description:
                product_list += f"   {product.description[:50]}...\n"
            product_list += "\n"

        product_list += "回复数字选择商品，或输入「取消」结束。"

        # 发送消息并更新会话状态
        if self.send_message(session.whatsapp_number, product_list):
            self._update_session_state(
                session,
                "selecting_product",
                {"products": [p.id for p in products]}
            )
            return {"action": "sent_product_list"}
        
        return {"action": "error", "error": "Failed to send product list"}

    def _handle_product_selection(
        self,
        session: models.WhatsAppSession,
        message: str
    ) -> Dict[str, Any]:
        """处理商品选择"""
        # 检查是否取消
        if message.lower() in ["取消", "cancel", "退出", "exit"]:
            self.send_message(
                session.whatsapp_number,
                "好的，已取消订单。如需帮助，随时联系我。"
            )
            self._update_session_state(session, "idle")
            return {"action": "cancelled"}

        try:
            # 解析选择的数字
            choice = int(message.strip())
            products = session.session_data.get("products", [])
            
            if not (1 <= choice <= len(products)):
                raise ValueError("Invalid choice")

            # 获取选中的商品
            product_id = products[choice - 1]
            product = product_service.get_product(self.db, product_id)

            if not product or not product.is_active or product.stock <= 0:
                self.send_message(
                    session.whatsapp_number,
                    "抱歉，该商品暂时无法购买。请选择其他商品。"
                )
                return self._send_product_list(session)

            # 发送数量输入提示
            msg = f"您选择了：{product.name}\n"
            msg += f"价格：${product.price}\n"
            msg += f"\n请输入购买数量（1-{min(product.stock, 10)}）："

            if self.send_message(session.whatsapp_number, msg):
                self._update_session_state(
                    session,
                    "entering_quantity",
                    {
                        "product_id": product_id,
                        "price": float(product.price)
                    }
                )
                return {"action": "product_selected", "product_id": product_id}

        except (ValueError, IndexError):
            self.send_message(session.whatsapp_number, "请输入有效的商品编号。")
            return {"action": "invalid_selection"}

        return {"action": "error", "error": "Failed to process product selection"}

    def _handle_quantity_input(
        self,
        session: models.WhatsAppSession,
        message: str
    ) -> Dict[str, Any]:
        """处理数量输入"""
        try:
            quantity = int(message.strip())
            product_id = session.session_data.get("product_id")
            product = product_service.get_product(self.db, product_id)

            if not product:
                raise ValueError("Product not found")

            if not (1 <= quantity <= min(product.stock, 10)):
                self.send_message(
                    session.whatsapp_number,
                    f"请输入有效数量（1-{min(product.stock, 10)}）。"
                )
                return {"action": "invalid_quantity"}

            # 计算总价
            total_price = quantity * session.session_data.get("price", 0)

            # 发送配送方式选择
            msg = f"数量：{quantity}\n"
            msg += f"总价：${total_price}\n\n"
            msg += "请选择配送方式：\n"
            for i, method in enumerate(product.delivery_methods, 1):
                msg += f"{i}. {method}\n"

            if self.send_message(session.whatsapp_number, msg):
                session_data = session.session_data
                session_data.update({
                    "quantity": quantity,
                    "total_price": total_price,
                    "delivery_methods": product.delivery_methods
                })
                self._update_session_state(session, "selecting_delivery", session_data)
                return {"action": "quantity_set", "quantity": quantity}

        except ValueError:
            self.send_message(session.whatsapp_number, "请输入有效的数字。")
            return {"action": "invalid_quantity"}

        return {"action": "error", "error": "Failed to process quantity"}

    def _handle_delivery_selection(
        self,
        session: models.WhatsAppSession,
        message: str
    ) -> Dict[str, Any]:
        """处理配送方式选择"""
        try:
            choice = int(message.strip())
            delivery_methods = session.session_data.get("delivery_methods", [])

            if not (1 <= choice <= len(delivery_methods)):
                self.send_message(
                    session.whatsapp_number,
                    "请选择有效的配送方式。"
                )
                return {"action": "invalid_delivery"}

            # 获取选中的配送方式
            delivery_method = delivery_methods[choice - 1]

            # 创建订单
            order_data = schemas.OrderCreate(
                customer_whatsapp=session.whatsapp_number,
                product_id=session.session_data.get("product_id"),
                quantity=session.session_data.get("quantity"),
                delivery_method=delivery_method
            )

            # 保存订单
            order = order_service.create_order(self.db, order_data)

            # 发送订单确认
            msg = "✅ 订单已确认！\n\n"
            msg += f"订单编号：#{order.id}\n"
            msg += f"商品：{order.product.name}\n"
            msg += f"数量：{order.quantity}\n"
            msg += f"总价：${order.total_price}\n"
            msg += f"配送方式：{order.delivery_method}\n\n"
            msg += "我们将尽快处理您的订单。"

            if self.send_message(session.whatsapp_number, msg):
                self._update_session_state(session, "idle")
                return {
                    "action": "order_created",
                    "order_id": order.id
                }

        except (ValueError, IndexError):
            self.send_message(session.whatsapp_number, "请选择有效的配送方式编号。")
            return {"action": "invalid_delivery"}
        except HTTPException as e:
            self.send_message(session.whatsapp_number, e.detail)
            return {"action": "error", "error": e.detail}

        return {"action": "error", "error": "Failed to process delivery selection"}