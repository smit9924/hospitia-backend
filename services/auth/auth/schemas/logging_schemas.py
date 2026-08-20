from pathlib import Path

from pydantic import computed_field

from auth.schemas.base_schemas import BaseSchema
from auth.types.enums import EnvironmentName, LogFormatName, LogLevelName


class LoggingSettings(BaseSchema):
    """Logging configuration passed to `configure_logging`."""

    environment: EnvironmentName
    service_name: str
    log_level: LogLevelName
    log_format: LogFormatName
    log_retention_days: int
    log_directory: Path

    @computed_field
    @property
    def use_file_handler(self) -> bool:
        """Local only. Production must never create log files."""
        return self.environment is EnvironmentName.LOCAL
