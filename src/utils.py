import time
import logging
from typing import TypeVar, Callable, Optional, Any
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    リトライデコレータ
    
    Args:
        max_attempts: 最大試行回数
        delay: 初回リトライまでの待機時間（秒）
        backoff: リトライごとの待機時間の倍率
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Optional[T]:
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed: {str(e)}. "
                            f"Retrying in {current_delay:.1f} seconds..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_attempts} attempts failed. Last error: {str(e)}")
            
            raise last_exception
        
        return wrapper
    return decorator