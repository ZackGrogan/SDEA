from dataclasses import dataclass
from datetime import datetime
import time
from typing import Dict, List, Optional
import psutil
import logging
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from functools import wraps
from .logger import monitoring_logger

# Prometheus metrics
REQUEST_COUNT = Counter('sec_app_requests_total', 'Total requests', ['endpoint'])
REQUEST_LATENCY = Histogram('sec_app_request_duration_seconds', 'Request latency')
ACTIVE_REQUESTS = Gauge('sec_app_active_requests', 'Active requests')
ERROR_COUNT = Counter('sec_app_errors_total', 'Total errors', ['type'])
CACHE_HITS = Counter('sec_app_cache_hits_total', 'Cache hits', ['cache_type'])
CACHE_MISSES = Counter('sec_app_cache_misses_total', 'Cache misses', ['cache_type'])
DB_CONNECTIONS = Gauge('sec_app_db_connections', 'Database connections')
API_RATE_LIMIT = Gauge('sec_app_api_rate_limit', 'API rate limit remaining')

@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""
    request_count: int
    average_latency: float
    error_count: int
    cache_hit_rate: float
    memory_usage: float
    cpu_usage: float
    active_connections: int

class MonitoringSystem:
    def __init__(self, metrics_port: int = 8000):
        """Initialize monitoring system"""
        self.start_time = datetime.now()
        self._initialize_prometheus(metrics_port)
        self.performance_history: List[Dict] = []
    
    def _initialize_prometheus(self, port: int):
        """Start Prometheus metrics server"""
        try:
            start_http_server(port)
            monitoring_logger.info(f"Prometheus metrics server started on port {port}")
        except Exception as e:
            monitoring_logger.error(f"Failed to start Prometheus server: {str(e)}")
    
    def track_request(self, endpoint: str):
        """Decorator to track request metrics"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                ACTIVE_REQUESTS.inc()
                REQUEST_COUNT.labels(endpoint=endpoint).inc()
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    ERROR_COUNT.labels(type=type(e).__name__).inc()
                    raise
                finally:
                    duration = time.time() - start_time
                    REQUEST_LATENCY.observe(duration)
                    ACTIVE_REQUESTS.dec()
            return wrapper
        return decorator
    
    def track_cache(self, cache_type: str, hit: bool):
        """Track cache hits and misses"""
        if hit:
            CACHE_HITS.labels(cache_type=cache_type).inc()
        else:
            CACHE_MISSES.labels(cache_type=cache_type).inc()
    
    def track_db_connections(self, count: int):
        """Track database connections"""
        DB_CONNECTIONS.set(count)
    
    def track_api_rate_limit(self, remaining: int):
        """Track API rate limit"""
        API_RATE_LIMIT.set(remaining)
    
    def get_system_metrics(self) -> Dict:
        """Get system resource metrics"""
        try:
            process = psutil.Process()
            return {
                'cpu_percent': process.cpu_percent(),
                'memory_percent': process.memory_percent(),
                'open_files': len(process.open_files()),
                'threads': process.num_threads(),
                'connections': len(process.connections())
            }
        except Exception as e:
            monitoring_logger.error(f"Error getting system metrics: {str(e)}")
            return {}
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics"""
        try:
            system_metrics = self.get_system_metrics()
            total_hits = sum(c.labels(cache_type='redis').get() for c in [CACHE_HITS])
            total_misses = sum(c.labels(cache_type='redis').get() for c in [CACHE_MISSES])
            
            return PerformanceMetrics(
                request_count=REQUEST_COUNT._value.sum(),
                average_latency=REQUEST_LATENCY.observe(0),
                error_count=ERROR_COUNT._value.sum(),
                cache_hit_rate=total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0,
                memory_usage=system_metrics.get('memory_percent', 0),
                cpu_usage=system_metrics.get('cpu_percent', 0),
                active_connections=system_metrics.get('connections', 0)
            )
        except Exception as e:
            monitoring_logger.error(f"Error calculating performance metrics: {str(e)}")
            return PerformanceMetrics(0, 0.0, 0, 0.0, 0.0, 0.0, 0)
    
    def record_metrics(self):
        """Record current metrics for historical tracking"""
        try:
            metrics = self.get_performance_metrics()
            self.performance_history.append({
                'timestamp': datetime.now().isoformat(),
                'metrics': metrics.__dict__
            })
            
            # Keep last 1000 records
            if len(self.performance_history) > 1000:
                self.performance_history.pop(0)
        except Exception as e:
            monitoring_logger.error(f"Error recording metrics: {str(e)}")
    
    def get_metrics_history(self, hours: Optional[int] = None) -> List[Dict]:
        """Get metrics history for specified hours"""
        try:
            if hours is None:
                return self.performance_history
            
            cutoff = datetime.now() - timedelta(hours=hours)
            return [
                record for record in self.performance_history
                if datetime.fromisoformat(record['timestamp']) >= cutoff
            ]
        except Exception as e:
            monitoring_logger.error(f"Error retrieving metrics history: {str(e)}")
            return []
