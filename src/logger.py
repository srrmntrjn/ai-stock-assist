"""Logging configuration for the trading bot."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Final

from loguru import Logger, logger

from src.config import settings

__all__ = ["log", "setup_logger"]

# Log formatting templates
CONSOLE_FORMAT: Final[str] = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
    "<level>{message}</level>"
)
FILE_FORMAT: Final[str] = (
    "{time:YYYY-MM-DD HH:mm:ss} | "
    "{level: <8} | "
    "{name}:{function}:{line} - {message}"
)
SUPPORTED_LOG_LEVELS: Final[frozenset[str]] = frozenset({
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
})
DEFAULT_LOG_LEVEL: Final[str] = "INFO"


def _resolve_log_level(level: str) -> str:
    """Return a valid log level name for Loguru."""
    normalized = level.upper()
    if normalized not in SUPPORTED_LOG_LEVELS:
        return DEFAULT_LOG_LEVEL
    return normalized


def setup_logger() -> Logger:
    """Configure Loguru with console and file handlers."""

    # Remove default logger configuration to avoid duplicate handlers
    logger.remove()

    # Ensure the log directory exists
    log_file = Path(settings.log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    log_level = _resolve_log_level(settings.log_level)

    # Console output with color
    logger.add(
        sys.stdout,
        format=CONSOLE_FORMAT,
        level=log_level,
        colorize=True,
    )

    # File output with rotation and compression
    logger.add(
        log_file,
        format=FILE_FORMAT,
        level=log_level,
        rotation="100 MB",
        retention="30 days",
        compression="zip",
    )

    logger.info(
        "Logger initialized - Level: {level}, File: {file}",
        level=log_level,
        file=str(log_file),
    )

    return logger


# Initialize logger when module is imported
log: Logger = setup_logger()
