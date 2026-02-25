"""
重試工具模塊
提供裝飾器和工具函數進行操作重試
"""

import time
from functools import wraps
from typing import Any, Callable
import random
from ..logger import log


def retry_with_backoff(
    retries: int = 3,
    backoff_in_seconds: int = 1,
    max_backoff_in_seconds: int = 10,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    帶指數退避的重試裝飾器
    
    參數:
        retries: 最大重試次數
        backoff_in_seconds: 初始退避時間（秒）
        max_backoff_in_seconds: 最大退避時間（秒）
        exceptions: 需要重試的異常類型
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            retry_backoff = backoff_in_seconds
            last_exception = None
            
            for retry_count in range(retries + 1):  # +1 for initial attempt
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if retry_count == retries:
                        log.error(
                            f"Max retries ({retries}) exceeded for {func.__name__}. "
                            f"Last error: {str(e)}"
                        )
                        raise
                    
                    # 計算下一次重試的延遲時間
                    jitter = random.uniform(0, 0.1 * retry_backoff)  # 添加隨機抖動
                    sleep_time = min(retry_backoff + jitter, max_backoff_in_seconds)
                    
                    log.warning(
                        f"Retry {retry_count + 1}/{retries} for {func.__name__} "
                        f"after {sleep_time:.2f}s. Error: {str(e)}"
                    )
                    
                    time.sleep(sleep_time)
                    retry_backoff *= 2  # 指數退避
            
            # 這裡理論上永遠不會到達
            raise last_exception
            
        return wrapper
    return decorator