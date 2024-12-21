import time
import functools
import random
from typing import Callable, Any, Optional, Type

from .logger import get_logger
from .exceptions import APIConnectionError, DataRetrievalError

logger = get_logger('retry_mechanism')

def exponential_backoff(
    base_delay: float = 1.0, 
    max_delay: float = 60.0, 
    max_retries: int = 5
) -> Callable:
    """
    Decorator to implement exponential backoff retry mechanism.
    
    Args:
        base_delay (float): Initial delay between retries
        max_delay (float): Maximum delay between retries
        max_retries (int): Maximum number of retry attempts
    
    Returns:
        Callable: Decorated function with retry mechanism
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except (APIConnectionError, DataRetrievalError) as e:
                    retries += 1
                    
                    # Calculate exponential backoff with jitter
                    delay = min(
                        max_delay, 
                        base_delay * (2 ** retries) + random.uniform(0, 0.1)
                    )
                    
                    logger.warning(
                        f"Retry attempt {retries}/{max_retries} for {func.__name__}. "
                        f"Error: {e}. Waiting {delay:.2f} seconds."
                    )
                    
                    time.sleep(delay)
            
            # Final attempt before giving up
            logger.error(f"Max retries reached for {func.__name__}")
            raise

        return wrapper
    return decorator

def retry_on_exception(
    exceptions: Optional[Type[Exception]] = None,
    max_retries: int = 3,
    delay: float = 1.0
) -> Callable:
    """
    Flexible retry decorator with configurable exceptions and retry strategy.
    
    Args:
        exceptions (Optional[Type[Exception]]): Exception types to catch
        max_retries (int): Maximum number of retry attempts
        delay (float): Fixed delay between retries
    
    Returns:
        Callable: Decorated function with retry mechanism
    """
    if exceptions is None:
        exceptions = (Exception,)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    
                    logger.warning(
                        f"Retry attempt {retries}/{max_retries} for {func.__name__}. "
                        f"Error: {e}. Waiting {delay} seconds."
                    )
                    
                    time.sleep(delay)
            
            # Final attempt before giving up
            logger.error(f"Max retries reached for {func.__name__}")
            raise
        
        return wrapper
    return decorator

def safe_execution(default_return: Any = None) -> Callable:
    """
    Decorator to safely execute functions with a default return value.
    
    Args:
        default_return (Any): Value to return if function execution fails
    
    Returns:
        Callable: Decorated function with safe execution
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Safe execution failed for {func.__name__}. "
                    f"Returning default value. Error: {e}"
                )
                return default_return
        return wrapper
    return decorator
