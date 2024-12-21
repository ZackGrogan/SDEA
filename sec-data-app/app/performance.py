import time
import functools
import logging
from typing import Callable, Any
from contextlib import contextmanager
import tracemalloc
import psutil
import os

from .logger import get_logger

performance_logger = get_logger('performance')

def measure_performance(func: Callable) -> Callable:
    """
    Decorator to measure function performance and log metrics.
    
    Args:
        func (Callable): Function to be measured
    
    Returns:
        Callable: Wrapped function with performance measurement
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tracemalloc.start()
        start_time = time.time()
        start_memory = tracemalloc.get_traced_memory()[0]
        
        try:
            result = func(*args, **kwargs)
            
            end_time = time.time()
            end_memory = tracemalloc.get_traced_memory()[0]
            
            execution_time = end_time - start_time
            memory_used = end_memory - start_memory
            
            performance_logger.info(
                f"Function: {func.__name__}, "
                f"Execution Time: {execution_time:.4f} seconds, "
                f"Memory Used: {memory_used / 1024:.2f} KB"
            )
            
            return result
        
        except Exception as e:
            performance_logger.error(
                f"Performance measurement failed for {func.__name__}: {e}"
            )
            raise
        finally:
            tracemalloc.stop()
    
    return wrapper

@contextmanager
def system_performance_context():
    """
    Context manager to track system-wide performance metrics.
    
    Tracks CPU usage, memory consumption, and disk I/O.
    """
    process = psutil.Process(os.getpid())
    
    # Initial system metrics
    start_cpu = process.cpu_percent()
    start_memory = process.memory_info().rss / (1024 * 1024)  # MB
    
    performance_logger.info("Starting system performance tracking")
    
    try:
        yield
    finally:
        # Final system metrics
        end_cpu = process.cpu_percent()
        end_memory = process.memory_info().rss / (1024 * 1024)  # MB
        
        performance_logger.info(
            f"System Performance: "
            f"CPU Usage Change: {end_cpu - start_cpu}%, "
            f"Memory Usage Change: {end_memory - start_memory:.2f} MB"
        )

def log_slow_functions(threshold_seconds: float = 1.0):
    """
    Decorator to log functions that exceed a specified execution time.
    
    Args:
        threshold_seconds (float): Execution time threshold in seconds
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if execution_time > threshold_seconds:
                performance_logger.warning(
                    f"Slow function detected: {func.__name__} "
                    f"took {execution_time:.4f} seconds to execute"
                )
            
            return result
        return wrapper
    return decorator

class PerformanceOptimizer:
    @staticmethod
    @measure_performance
    def parallel_process(func: Callable, items: list, max_workers: int = None) -> list:
        """
        Execute function in parallel across multiple CPU cores
        
        :param func: Function to execute
        :param items: List of items to process
        :param max_workers: Maximum number of worker processes
        :return: List of processed results
        """
        if max_workers is None:
            max_workers = multiprocessing.cpu_count()
        
        try:
            with multiprocessing.Pool(processes=max_workers) as pool:
                results = pool.map(func, items)
            return results
        except Exception as e:
            performance_logger.error(f'Parallel processing error: {e}')
            return []

    @staticmethod
    def batch_processing(data: list, batch_size: int = 100):
        """
        Process data in batches to manage memory and improve performance
        
        :param data: List of items to process
        :param batch_size: Number of items per batch
        :return: Generator of processed batches
        """
        for i in range(0, len(data), batch_size):
            yield data[i:i + batch_size]

def optimize_data_processing(data):
    """
    Comprehensive data processing optimization
    
    :param data: Input data to process
    :return: Optimized processed data
    """
    optimizer = PerformanceOptimizer()
    
    # Example optimization strategy
    processed_batches = []
    for batch in optimizer.batch_processing(data):
        processed_batch = optimizer.parallel_process(
            func=_process_item,  # Define this function based on your specific processing needs
            items=batch
        )
        processed_batches.extend(processed_batch)
    
    return processed_batches

def _process_item(item):
    """
    Placeholder for item-level processing logic
    Customize this function for your specific data processing needs
    """
    # Implement specific processing logic here
    return item
