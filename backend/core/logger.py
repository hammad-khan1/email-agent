"""
Centralized logging configuration using Loguru.
"""

import sys
from pathlib import Path
from loguru import logger


LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


def setup_logger() -> None:
    """Configure Loguru with console and file sinks."""
    logger.remove()  # Remove default handler

    # Console — colored output
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> — <level>{message}</level>",
        level="INFO",
    )

    # File — rotating daily logs
    logger.add(
        LOG_DIR / "app_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} — {message}",
        level="DEBUG",
    )

    # Separate error log
    logger.add(
        LOG_DIR / "errors.log",
        rotation="10 MB",
        retention="60 days",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{line} — {message}\n{exception}",
    )

    logger.info("Logger initialized.")
