"""Structured logging configuration using loguru"""

import sys
from loguru import logger
from app.core.config import settings

# Remove default handler
logger.remove()

# Add custom handler with structured format
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
    level=settings.LOG_LEVEL,
    colorize=True,
)

# Add file handler for persistent logs
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    level=settings.LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
    serialize=False,
)

# Add JSON file handler for structured logs
logger.add(
    "logs/app_{time:YYYY-MM-DD}.json",
    rotation="00:00",
    retention="30 days",
    level=settings.LOG_LEVEL,
    serialize=True,
)


def log_event(event_type: str, **kwargs):
    """Log structured event with additional context"""
    logger.info(f"EVENT: {event_type}", extra=kwargs)


def log_error(error_type: str, error: Exception, **kwargs):
    """Log structured error with additional context"""
    logger.error(f"ERROR: {error_type} - {str(error)}", extra=kwargs)


def log_metric(metric_name: str, value: float, **kwargs):
    """Log metric for monitoring"""
    logger.info(f"METRIC: {metric_name}={value}", extra=kwargs)
