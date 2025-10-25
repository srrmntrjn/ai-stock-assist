"""Logging configuration for the trading bot"""

import sys
from pathlib import Path
from loguru import logger
from src.config import settings


def setup_logger():
    """Configure loguru logger with file and console output"""

    # Remove default logger
    logger.remove()

    # Create logs directory if it doesn't exist
    log_file = Path(settings.log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Console output with color
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True,
    )

    # File output with rotation
    logger.add(
        settings.log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.log_level,
        rotation="100 MB",
        retention="30 days",
        compression="zip",
    )

    logger.info(f"Logger initialized - Level: {settings.log_level}, File: {settings.log_file}")

    return logger


# Initialize logger when module is imported
log = setup_logger()
