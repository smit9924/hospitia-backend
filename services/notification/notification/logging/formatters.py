import json
from datetime import UTC, datetime
from logging import Formatter, LogRecord


class ConsoleFormatter(Formatter):
    """Human-readable local formatter."""

    def format(self, record: LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        service_name = getattr(record, "service_name", "-")
        request_id = getattr(record, "request_id", "-")
        location = f"{record.name}.{record.funcName}"
        message = record.getMessage()
        if record.exc_info:
            message = f"{message}\n{self.formatException(record.exc_info)}"
        return (
            f"{record.levelname} | {timestamp} | {service_name} | "
            f"request_id={request_id} | {location} | {message}"
        )


class JsonFormatter(Formatter):
    """Structured JSON formatter compatible with Loki label/query workflows."""

    def format(self, record: LogRecord) -> str:
        payload: dict[str, str] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "request_id": getattr(record, "request_id", "-"),
            "service": getattr(record, "service_name", "-"),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)
