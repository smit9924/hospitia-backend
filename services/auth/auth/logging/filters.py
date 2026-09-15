from logging import Filter, LogRecord

from auth.middleware.request_context import get_request_id


class ContextFilter(Filter):
    """Inject service name and request ID into every log record."""

    def __init__(self, service_name: str) -> None:
        super().__init__()
        self._service_name = service_name

    def filter(self, record: LogRecord) -> bool:
        record.service_name = self._service_name
        record.request_id = get_request_id()
        return True
