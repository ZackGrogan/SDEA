import os
import uuid
import logging
from logging.handlers import RotatingFileHandler
import structlog

def setup_root_logger():
    """
    Sets up the root logger with a rotating file handler.
    Configures both standard logging and structlog.
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # Generate unique session ID for log file
    session_id = uuid.uuid4()
    log_file = os.path.join(log_dir, f'session_{session_id}.log')

    # Configure standard logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(name)s - %(funcName)s:%(lineno)d - %(message)s',
        handlers=[
            RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5,
                mode='a'
            ),
            logging.StreamHandler()  # Also log to console
        ]
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Set file permissions for log file
    try:
        os.chmod(log_file, 0o600)
    except Exception as e:
        logging.error(f"Could not set log file permissions: {e}")

    return logging.getLogger()

def get_logger(name=None):
    """
    Get a structured logger with optional name.
    
    :param name: Optional logger name. If None, uses root logger.
    :return: Configured logger
    """
    if name is None:
        return structlog.get_logger()
    return structlog.get_logger(name)

# Initialize logging on module import
setup_root_logger()
