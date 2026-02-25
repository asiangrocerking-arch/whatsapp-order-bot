"""
日誌配置模塊
提供結構化日誌記錄
"""

import sys
import logging
from pathlib import Path
from loguru import logger
import json
from datetime import datetime

# 創建日誌目錄
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# 移除默認處理器
logger.remove()

# 添加控制台處理器（開發環境用）
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

# 添加文件處理器（JSON格式，用於生產環境分析）
logger.add(
    "logs/app.json",
    serialize=True,  # JSON格式
    format="{message}",  # message將是一個JSON字符串
    rotation="500 MB",  # 每500MB輪換一次
    retention="10 days",  # 保留10天
    level="INFO",
    encoding="utf-8"
)

# 添加錯誤日誌處理器
logger.add(
    "logs/error.log",
    format="<red>{time:YYYY-MM-DD HH:mm:ss}</red> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="ERROR",
    rotation="100 MB",
    retention="7 days",
    backtrace=True,  # 顯示完整的堆棧跟踪
    diagnose=True    # 顯示變量值
)

class InterceptHandler(logging.Handler):
    """
    將標準庫日誌轉發到loguru
    """
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

# 配置標準庫日誌
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

# 替換uvicorn和gunicorn的日誌處理器
logging.getLogger("uvicorn").handlers = [InterceptHandler()]
logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
logging.getLogger("gunicorn").handlers = [InterceptHandler()]

# 導出logger實例
log = logger