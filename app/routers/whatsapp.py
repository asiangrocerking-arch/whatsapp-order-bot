"""
WhatsApp Webhook API 路由
"""

from fastapi import APIRouter, Request, Depends, HTTPException, status
from twilio.twiml.messaging_response import MessagingResponse
from sqlalchemy.orm import Session
import logging
from typing import Dict, Any

from ..database import get_db
from ..services.whatsapp_service import WhatsAppService

router = APIRouter(
    prefix="/webhook",
    tags=["whatsapp"]
)

# 設置日誌
logger = logging.getLogger(__name__)


@router.post("/whatsapp")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Twilio WhatsApp Webhook 端點
    接收和處理 WhatsApp 消息
    """
    try:
        form_data = await request.form()
        
        # 提取消息信息
        from_number = form_data.get("From", "")
        to_number = form_data.get("To", "")
        message_body = form_data.get("Body", "")
        num_media = form_data.get("NumMedia", "0")
        
        logger.info(f"WhatsApp message received - From: {from_number}, Body: {message_body[:50]}...")
        
        # 檢查是否是群組消息
        is_group = False
        if from_number.endswith("@g.us"):
            is_group = True
            logger.info(f"Group message detected from {from_number}")
        
        # 初始化 WhatsApp 服務
        whatsapp_service = WhatsAppService(db)
        
        # 處理消息
        result = whatsapp_service.handle_incoming_message(
            from_number=from_number,
            message_body=message_body,
            is_group=is_group
        )
        
        logger.info(f"Message processed - Action: {result.get('action')}")
        
        # 返回 Twilio 響應
        resp = MessagingResponse()
        return str(resp)
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}", exc_info=True)
        
        # 即使出錯，也要返回成功響應給 Twilio，避免重試
        resp = MessagingResponse()
        return str(resp)


@router.get("/whatsapp")
async def whatsapp_webhook_verify(request: Request):
    """
    Twilio WhatsApp Webhook 驗證端點
    Twilio 在設置 webhook 時會發送 GET 請求驗證
    """
    return {"status": "ok", "message": "WhatsApp webhook is ready"}


@router.post("/whatsapp/send")
async def send_whatsapp_message(
    request_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    發送 WhatsApp 消息（管理員手動發送）
    """
    to_number = request_data.get("to_number")
    message = request_data.get("message")
    media_url = request_data.get("media_url")
    
    if not to_number or not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少必要參數：to_number 和 message"
        )
    
    whatsapp_service = WhatsAppService(db)
    success = whatsapp_service.send_message(to_number, message, media_url)
    
    if success:
        return {"status": "success", "message": "WhatsApp message sent"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send WhatsApp message"
        )


@router.get("/whatsapp/sessions")
async def get_whatsapp_sessions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    獲取 WhatsApp 會話列表（管理員查看）
    """
    from .. import models
    
    sessions = db.query(models.WhatsAppSession).order_by(
        models.WhatsAppSession.last_interaction.desc()
    ).offset(skip).limit(limit).all()
    
    return sessions


@router.delete("/whatsapp/sessions/{whatsapp_number}")
async def delete_whatsapp_session(
    whatsapp_number: str,
    db: Session = Depends(get_db)
):
    """
    刪除 WhatsApp 會話（管理員操作）
    """
    from .. import models
    
    session = db.query(models.WhatsAppSession).filter(
        models.WhatsAppSession.whatsapp_number == whatsapp_number
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="會話不存在"
        )
    
    db.delete(session)
    db.commit()
    
    return {"status": "success", "message": "會話已刪除"}


@router.get("/whatsapp/test")
async def test_whatsapp_integration(db: Session = Depends(get_db)):
    """
    測試 WhatsApp 集成狀態
    """
    import os
    
    config_status = {
        "twilio_account_sid": bool(os.getenv("TWILIO_ACCOUNT_SID")),
        "twilio_auth_token": bool(os.getenv("TWILIO_AUTH_TOKEN")),
        "twilio_whatsapp_number": os.getenv("TWILIO_WHATSAPP_NUMBER", "Not set"),
        "webhook_url": "Set in Twilio console"
    }
    
    return {
        "status": "ok",
        "config": config_status,
        "message": "Check Twilio console for webhook configuration"
    }