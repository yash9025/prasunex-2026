"""Structured logging configuration for LearningBridge.

Outputs structured JSON logs for auditability, telemetry, and clean debugging.
"""

import logging
import sys
from typing import Any, Dict
from pythonjsonlogger.json import JsonFormatter


class CustomJsonFormatter(JsonFormatter):
    """Formats log records into structured JSON with standard contextual fields."""

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["service"] = "learningbridge-backend"
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        if "request_id" not in log_record:
            log_record["request_id"] = getattr(record, "request_id", None)
        if "school_id" not in log_record:
            log_record["school_id"] = getattr(record, "school_id", None)
        if "user_id" not in log_record:
            log_record["user_id"] = getattr(record, "user_id", None)


def setup_logging(debug: bool = False) -> logging.Logger:
    """Configures the root logger with JSON formatting."""
    log_level = logging.DEBUG if debug else logging.INFO
    logger = logging.getLogger("learningbridge")
    logger.setLevel(log_level)

    # Avoid duplicate handlers if setup is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = CustomJsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False

    return logger


logger = setup_logging()
