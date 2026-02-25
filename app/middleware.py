"""
中間件模塊
包含請求限流、日誌記錄等中間件
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from collections import defaultdict
import time
import logging
from typing import Callable, Dict, List
from datetime import datetime
from .config import settings
from .logger import log

class RateLimiter:
    """
    簡單的內存限流器
    使用滑動窗口算法
    """
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[float]] = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        minute_ago = now - 60
        
        # 清理舊請求
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > minute_ago
        ]
        
        # 檢查是否超過限制
        if len(self.requests[client_id]) >= self.requests_per_minute:
            return False
        
        self.requests[client_id].append(now)
        return True
    
    def get_remaining(self, client_id: str) -> int:
        """獲取剩餘請求次數"""
        now = time.time()
        minute_ago = now - 60
        
        # 清理舊請求
        current_requests = [
            req_time for req_time in self.requests.get(client_id, [])
            if req_time > minute_ago
        ]
        self.requests[client_id] = current_requests
        
        return max(0, self.requests_per_minute - len(current_requests))


# 創建限流器實例
rate_limiter = RateLimiter(settings.RATE_LIMIT_PER_MINUTE)


async def rate_limit_middleware(
    request: Request,
    call_next: Callable
) -> Response:
    """
    請求限流中間件
    """
    # 跳過健康檢查
    if request.url.path == "/health":
        return await call_next(request)
    
    client_id = request.client.host
    remaining = rate_limiter.get_remaining(client_id)
    
    # 添加剩餘請求次數到響應頭
    response = Response()
    response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    
    if not rate_limiter.is_allowed(client_id):
        log.warning(f"Rate limit exceeded for client {client_id}")
        return JSONResponse(
            status_code=429,
            content={
                "error": "Too many requests",
                "detail": "請求頻率超過限制，請稍後再試"
            },
            headers=response.headers
        )
    
    try:
        response = await call_next(request)
        
        # 將限流信息添加到響應頭
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Remaining"] = str(remaining - 1)
        
        return response
        
    except Exception as e:
        log.exception(f"Error processing request: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"},
            headers=response.headers
        )


async def logging_middleware(
    request: Request,
    call_next: Callable
) -> Response:
    """
    請求日誌中間件
    記錄請求和響應信息
    """
    start_time = time.time()
    
    # 準備日誌數據
    log_data = {
        "client_ip": request.client.host,
        "timestamp": datetime.now().isoformat(),
        "method": request.method,
        "path": request.url.path,
        "query_params": str(request.query_params),
        "headers": dict(request.headers),
    }
    
    try:
        response = await call_next(request)
        
        # 添加響應信息
        log_data.update({
            "status_code": response.status_code,
            "processing_time": f"{(time.time() - start_time):.3f}s"
        })
        
        # 根據狀態碼決定日誌級別
        if response.status_code >= 500:
            log.error(log_data)
        elif response.status_code >= 400:
            log.warning(log_data)
        else:
            log.info(log_data)
        
        return response
        
    except Exception as e:
        log_data.update({
            "error": str(e),
            "processing_time": f"{(time.time() - start_time):.3f}s"
        })
        log.exception(log_data)
        raise