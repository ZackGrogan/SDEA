import asyncio
import time
from .logger import rate_limit_logger
from typing import Optional

class RateLimiter:
    def __init__(
        self, 
        max_requests: int = 10, 
        per_seconds: float = 1.0,
        burst_limit: Optional[int] = None
    ):
        """
        Initialize rate limiter with configurable rate limits.
        
        :param max_requests: Maximum number of requests allowed
        :param per_seconds: Time window for max requests
        :param burst_limit: Maximum number of requests that can be made in burst
        """
        self._lock = asyncio.Lock()
        self.max_requests = max_requests
        self.per_seconds = per_seconds
        self.burst_limit = burst_limit or max_requests
        
        self.request_times = []
        
        # Log any unexpected arguments for debugging
        if burst_limit is None:
            rate_limit_logger.warning("Burst limit not specified, using max requests as burst limit")
    
    async def __aenter__(self):
        async with self._lock:
            current_time = time.time()
            
            # Remove timestamps outside the current time window
            self.request_times = [
                t for t in self.request_times 
                if current_time - t < self.per_seconds
            ]
            
            # Check burst limit
            if len(self.request_times) >= self.burst_limit:
                oldest_request_time = min(self.request_times)
                sleep_time = self.per_seconds - (current_time - oldest_request_time)
                if sleep_time > 0:
                    rate_limit_logger.info(f"Rate limit reached. Waiting {sleep_time:.2f} seconds.")
                    await asyncio.sleep(sleep_time)
            
            # Add current request timestamp
            self.request_times.append(current_time)
            return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def wait(self):
        """
        Synchronous wait method for rate limiting.
        Blocks the current thread if rate limit is exceeded.
        """
        current_time = time.time()
        
        # Remove timestamps outside the current time window
        self.request_times = [
            t for t in self.request_times 
            if current_time - t < self.per_seconds
        ]
        
        # Check burst limit
        if len(self.request_times) >= self.burst_limit:
            oldest_request_time = min(self.request_times)
            sleep_time = self.per_seconds - (current_time - oldest_request_time)
            if sleep_time > 0:
                rate_limit_logger.info(f"Rate limit reached. Waiting {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)
        
        # Add current request timestamp
        self.request_times.append(current_time)

def exponential_backoff(
    max_retries: int = 3, 
    base_delay: float = 1.0, 
    max_delay: float = 60.0
) -> float:
    """
    Calculate exponential backoff time with jitter.
    
    :param max_retries: Maximum number of retry attempts
    :param base_delay: Base delay time in seconds
    :param max_delay: Maximum delay time in seconds
    :return: Calculated backoff time
    """
    import random
    
    def backoff(retry_count):
        delay = min(
            max_delay, 
            base_delay * (2 ** retry_count)
        )
        # Add randomness to prevent thundering herd problem
        jitter = random.uniform(0, 0.1 * delay)
        return delay + jitter
    
    return backoff
