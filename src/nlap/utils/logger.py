"""Structured logging configuration using structlog for OpenSearch compatibility."""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from nlap.config.settings import get_settings


def add_app_context(_: logging.Logger, __: str, event_dict: EventDict) -> EventDict:
    """Add application context to log events."""
    settings = get_settings()
    event_dict["app_name"] = settings.app.app_name
    event_dict["environment"] = settings.app.environment
    return event_dict


def drop_color_message_key(_: logging.Logger, __: str, event_dict: EventDict) -> EventDict:
    """Remove the color_message key if it exists."""
    event_dict.pop("color_message", None)
    return event_dict


def setup_logging() -> None:
    """Configure structured logging for production use with JSON output."""
    settings = get_settings()

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.app.log_level.upper(), logging.INFO),
    )

    # Configure structlog processors
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,  # Merge context variables
        structlog.stdlib.add_log_level,  # Add log level
        structlog.stdlib.add_logger_name,  # Add logger name
        structlog.stdlib.ExtraAdder(),  # Add extra fields
        add_app_context,  # Add application context
        structlog.processors.TimeStamper(fmt="iso"),  # Add ISO timestamp
        structlog.processors.StackInfoRenderer(),  # Add stack info for exceptions
        structlog.processors.format_exc_info,  # Format exceptions
        drop_color_message_key,  # Remove color_message if present
    ]

    # Add JSON renderer for production (OpenSearch compatible)
    if settings.app.environment == "production" or not settings.app.debug:
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Use console renderer for development
        processors.append(
            structlog.dev.ConsoleRenderer(colors=True)
        )

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a configured structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger instance
    """
    return structlog.get_logger(name)


def bind_request_context(request_id: str, **kwargs: Any) -> None:
    """Bind request context variables for distributed tracing.

    Args:
        request_id: Unique request identifier
        **kwargs: Additional context variables (e.g., user_id, correlation_id)
    """
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id, **kwargs)


def clear_request_context() -> None:
    """Clear request context variables."""
    structlog.contextvars.clear_contextvars()

