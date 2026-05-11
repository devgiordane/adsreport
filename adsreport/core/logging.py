"""structlog setup: JSON in production, colorized in development."""

from __future__ import annotations

import logging
import os
import sys

import structlog


def setup_logging(debug: bool | None = None) -> None:
    if debug is None:
        debug = os.environ.get("ADSREPORT_DEBUG", "").lower() in ("1", "true", "yes")

    level = logging.DEBUG if debug else logging.INFO

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if debug or not _is_json_output():
        processors: list[structlog.types.Processor] = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty()),
        ]
    else:
        processors = [
            *shared_processors,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=level,
    )


def _is_json_output() -> bool:
    return not sys.stderr.isatty()


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    return structlog.get_logger(name)
