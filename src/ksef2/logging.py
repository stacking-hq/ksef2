import logging
from typing import Any, Literal, Protocol

import structlog

DEFAULT_LOGGER_NAME = "ksef2"

_SHARED_PROCESSORS: list[Any] = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
]


class LoggerProtocol(Protocol):
    def info(self, event: str | None = None, **kw: object) -> object: ...
    def warning(self, event: str | None = None, **kw: object) -> object: ...
    def error(self, event: str | None = None, **kw: object) -> object: ...
    def exception(self, event: str | None = None, **kw: object) -> object: ...
    def bind(self, **new_values: object) -> "LoggerProtocol": ...


def get_logger(name: str | None = None, **initial_values: object) -> LoggerProtocol:
    """Return a package logger without configuring global logging on import."""
    return structlog.get_logger(name or DEFAULT_LOGGER_NAME, **initial_values)  # type: ignore[return-value]


def configure_logging(
    *,
    level: int | str = logging.INFO,
    renderer: Literal["console", "json"] = "console",
    stream: Any | None = None,
    force: bool = False,
) -> None:
    """Configure standard logging and structlog for applications using the SDK.

    Libraries should not call this automatically. Applications may use this
    helper for a sensible default or configure structlog themselves.
    """
    final_renderer = (
        structlog.processors.JSONRenderer()
        if renderer == "json"
        else structlog.dev.ConsoleRenderer()
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=list(_SHARED_PROCESSORS),
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            final_renderer,
        ],
    )

    handler = logging.StreamHandler(stream)
    handler.setFormatter(formatter)

    logging.basicConfig(level=level, handlers=[handler], force=force)

    structlog.configure(
        processors=[
            *_SHARED_PROCESSORS,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        # Do not cache: applications may call configure_logging() after
        # get_logger() is called at module import time.
        cache_logger_on_first_use=False,
    )
