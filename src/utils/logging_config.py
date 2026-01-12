"""Structured logging configuration for production."""

import sys
import logging
from typing import Optional

# Try to import structlog, fallback to standard logging if not available
try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False


def setup_logging(level: str = "INFO", json_logs: bool = True):
    """Configure structured logging for production."""
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    if STRUCTLOG_AVAILABLE and json_logs:
        # Configure standard library logging
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=log_level,
        )
        
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
        ]
        
        if json_logs:
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.append(structlog.dev.ConsoleRenderer())
        
        structlog.configure(
            processors=processors,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        return structlog.get_logger()
    else:
        # Fallback to standard logging
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            stream=sys.stdout,
            level=log_level,
        )
        return logging.getLogger()


def get_logger(name: Optional[str] = None):
    """Get a logger instance."""
    if STRUCTLOG_AVAILABLE:
        return structlog.get_logger(name)
    else:
        return logging.getLogger(name)

