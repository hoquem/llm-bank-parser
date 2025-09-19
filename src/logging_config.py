"""
Logging configuration for the bank statement processor.

This module sets up structured logging using structlog with consistent
formatting and appropriate log levels.
"""

import logging
import sys
from typing import Any, Dict

import structlog


def setup_logging(level: str = "INFO") -> None:
    """
    Configure structured logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Configure standard library logging
    logging.basicConfig(
        level=numeric_level,
        format="%(message)s",
        stream=sys.stdout,
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
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structured logger
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """
    Mixin class to provide logging capabilities to other classes.
    """

    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Get a logger instance for this class."""
        return get_logger(self.__class__.__module__)

    def log_operation(self, operation: str, **kwargs: Any) -> None:
        """
        Log an operation with structured data.

        Args:
            operation: Operation description
            **kwargs: Additional structured data
        """
        self.logger.info(operation, **kwargs)

    def log_error(self, error: str, exception: Exception = None, **kwargs: Any) -> None:
        """
        Log an error with structured data.

        Args:
            error: Error description
            exception: Exception instance if available
            **kwargs: Additional structured data
        """
        log_data = {"error": error, **kwargs}
        if exception:
            log_data["exception_type"] = type(exception).__name__
            log_data["exception_message"] = str(exception)

        self.logger.error("Operation failed", **log_data)

    def log_progress(self, current: int, total: int, item: str = None, **kwargs: Any) -> None:
        """
        Log progress information.

        Args:
            current: Current item number
            total: Total items
            item: Current item description
            **kwargs: Additional structured data
        """
        progress_data = {
            "progress_current": current,
            "progress_total": total,
            "progress_percentage": round((current / total) * 100, 1) if total > 0 else 0,
            **kwargs
        }

        if item:
            progress_data["current_item"] = item

        self.logger.info("Processing progress", **progress_data)