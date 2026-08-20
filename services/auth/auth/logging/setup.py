import logging
import sys
from logging.handlers import TimedRotatingFileHandler

from auth.logging.filters import ContextFilter
from auth.logging.formatters import ConsoleFormatter, JsonFormatter
from auth.schemas.logging_schemas import LoggingSettings
from auth.types.enums import LogFormatName

_PROPAGATING_LOGGERS = ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi")

_FORMATTERS = {
    LogFormatName.JSON: JsonFormatter,
    LogFormatName.CONSOLE: ConsoleFormatter,
}


def configure_logging(settings: LoggingSettings) -> None:
    """
    Configure process-wide logging. Safe to call again under uvicorn --reload.

    Production never attaches a file handler. Local writes daily files and console.
    """
    formatter = _FORMATTERS[settings.log_format]()
    context_filter = ContextFilter(settings.service_name)
    level = logging.getLevelNamesMapping()[settings.log_level]

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(context_filter)

    handlers: list[logging.Handler] = [stream_handler]

    if settings.use_file_handler:
        settings.log_directory.mkdir(parents=True, exist_ok=True)
        file_handler = TimedRotatingFileHandler(
            filename=str(settings.log_directory / f"{settings.service_name}.log"),
            when="midnight",
            interval=1,
            backupCount=settings.log_retention_days,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(context_filter)
        handlers.append(file_handler)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    for handler in handlers:
        root_logger.addHandler(handler)

    for logger_name in _PROPAGATING_LOGGERS:
        named_logger = logging.getLogger(logger_name)
        named_logger.handlers.clear()
        named_logger.propagate = True
        named_logger.setLevel(level)
