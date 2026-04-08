"""
Logging configuration using loguru.
Provides structured logging with file rotation and console output.
"""

import sys
from pathlib import Path

from loguru import logger

from app.core.config import settings


def setup_logging():
    """
    Configure loguru logger with console and file handlers.
    """
    # Remove default handler
    logger.remove()

    # Determine log level based on environment
    log_level = settings.LOG_LEVEL.upper()

    # Console handler with colored output
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>",
        colorize=True,
    )

    # File handler with rotation
    if settings.LOG_FILE:
        # Ensure log directory exists
        log_path = Path(settings.LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            settings.LOG_FILE,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation=settings.LOG_ROTATION,
            retention=settings.LOG_RETENTION,
            compression="zip",
            encoding="utf-8",
        )

    # JSON format for production
    if settings.is_production:
        logger.add(
            sys.stdout,
            level="INFO",
            format='{{"timestamp": "{time:YYYY-MM-DDTHH:mm:ssZ}", "level": "{level}", "message": "{message}", "module": "{name}", "function": "{function}", "line": {line}}}',
            serialize=True,
        )

    logger.info(f"Logging configured with level: {log_level}")


def get_logger(name: str = None):
    """
    Get a logger instance with optional name binding.
    """
    if name:
        return logger.bind(name=name)
    return logger
