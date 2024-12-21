import logging
import logging.config
import os
import uuid
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime

def get_correlation_id():
    """Generate a unique correlation ID for tracing requests."""
    return str(uuid.uuid4())

class CorrelationIdFilter(logging.Filter):
    """Logging filter to add correlation ID to log records."""
    def __init__(self, correlation_id=None):
        super().__init__()
        self.correlation_id = correlation_id or get_correlation_id()

    def filter(self, record):
        record.correlation_id = self.correlation_id
        return True

def setup_logging(log_level='INFO', log_format=None):
    """
    Configure logging with advanced features.
    
    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format (str, optional): Custom log format
    """
    # Ensure logs directory exists
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # Generate unique log filename
    log_filename = f"sec_data_app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_path = os.path.join(log_dir, log_filename)

    # Default log format with correlation ID
    default_format = (
        '%(asctime)s - %(levelname)s - '
        'correlation_id=%(correlation_id)s - '
        '%(name)s:%(funcName)s:%(lineno)d - %(message)s'
    )

    # Logging configuration
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': log_format or default_format,
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'json': {
                '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                'format': '%(asctime)s %(levelname)s %(name)s %(message)s'
            }
        },
        'filters': {
            'correlation_id': {
                '()': CorrelationIdFilter
            }
        },
        'handlers': {
            'console': {
                'level': log_level,
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'filters': ['correlation_id']
            },
            'file': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': log_path,
                'maxBytes': 10 * 1024 * 1024,  # 10MB
                'backupCount': 5,
                'formatter': 'standard',
                'filters': ['correlation_id']
            }
        },
        'loggers': {
            '': {  # Root logger
                'handlers': ['console', 'file'],
                'level': log_level,
                'propagate': True
            }
        }
    }

    logging.config.dictConfig(logging_config)
    return logging.getLogger()

# Initialize logging on import
root_logger = setup_logging()

def get_logger(name):
    """
    Get a logger with the specified name.
    
    Args:
        name (str): Name of the logger
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.addFilter(CorrelationIdFilter())
    return logger

# Predefined loggers for different components
sec_filings_logger = get_logger('sec_filings')
market_data_logger = get_logger('market_data')
data_parsing_logger = get_logger('data_parsing')
data_enrichment_logger = get_logger('data_enrichment')
rate_limit_logger = get_logger('rate_limit')
app_logger = get_logger('app')
cache_logger = get_logger('cache')
enrichment_logger = get_logger('enrichment')

# Export all loggers for use in other modules
__all__ = [
    'sec_filings_logger',
    'market_data_logger',
    'data_parsing_logger',
    'data_enrichment_logger',
    'rate_limit_logger',
    'app_logger',
    'cache_logger',
    'enrichment_logger'
]