from os import path
from pathlib import Path

from pika.exchange_type import ExchangeType
from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from payment.schemas.logging_schemas import LoggingSettings
from payment.types.enums import EnvironmentName, LogFormatName, LogLevelName

BASE_DIR: Path = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file = path.join(BASE_DIR, "../", ".env"),
        env_ignore_empty = True,
        extra = "ignore",
    )

    app_name: str = "Payment Service"


    API_V1_STR: str = "/api/v1"  # Base path for API version 1 endpoints

    ENVIRONMENT: EnvironmentName = ...  # type: ignore
    SERVICE_NAME: str = ...  # type: ignore
    LOG_LEVEL: LogLevelName = ...  # type: ignore
    LOG_FORMAT: LogFormatName = ...  # type: ignore
    LOG_RETENTION_DAYS: int = ...  # type: ignore


    # Ignore Pylance type checks here. These fields are populated by Pydantic Settings at runtime,
    # and the application should fail loudly if any required environment variable is missing.

    # CORS
    ALLOWED_ORIGINS: list[str] = ... # type: ignore
    ALLOWED_CREDENTIALS: bool = ... # type: ignore
    ALLOWED_METHODS: list[str] = ... # type: ignore
    ALLOWED_HEADERS: list[str] = ... # type: ignore

    # Postgres configuration
    POSTGRES_SERVER: str = ... # type: ignore
    POSTGRES_PORT: int = ... # type: ignore
    POSTGRES_DB: str = ... # type: ignore
    POSTGRES_USER: str = ... # type: ignore
    POSTGRES_PASSWORD: str = ... # type: ignore

    # JWT configuration
    JWT_ENCRYPTION_ALGORITHM: str = ... # type: ignore
    JWT_ENCRYPTION_SECRET_KEY: str = ... # type: ignore

    MQ_CLIENT_TYPE: str = ... # type: ignore

    # RabbitMQ
    RABBITMQ_HOST: str = ...  # type: ignore
    RABBITMQ_PORT: int = ...  # type: ignore
    RABBITMQ_HEART_BEAT: int = ...  # type: ignore
    RABBITMQ_CONNECTION_TIMEOUT: int = ...  # type: ignore
    RABBITMQ_RETRY_ATTEMPTS: int = ...  # type: ignore
    RABBITMQ_RETRY_DELAY: int = ...  # type: ignore
    RABBITMQ_USERNAME: str = ...  # type: ignore
    RABBITMQ_PASSWORD: str = ...  # type: ignore
    RABBITMQ_PUBLISH_RETRY_ATTEMPTS: int = ...  # type: ignore
    RABBITMQ_PUBLISH_RETRY_DELAY: int = ...  # type: ignore
    RABBITMQ_CONSUMER_RETRY_DELAY: int = ...  # type: ignore
    RABBITMQ_CONSUMER_PREFETCH_COUNT: int = ...  # type: ignore

    # Notification topology
    EMAIL_NOTIFICATION_EXCHANGE: str = ... # type: ignore
    EMAIL_NOTIFICATION_EXCHANGE_TYPE: ExchangeType = ... # type: ignore
    FORGOT_PASSWORD_EMAIL_QUEUE: str = ... # type: ignore
    FORGOT_PASSWORD_EMAIL_QUEUE_ROUTING_KEY: str = ... # type: ignore

    USER_EVENTS_EXCHANGE: str = ... # type: ignore
    USER_EVENTS_EXCHANGE_TYPE: ExchangeType = ... # type: ignore
    USER_CREATED_QUEUE: str = ... # type: ignore
    USER_CREATED_QUEUE_ROUTING_KEY: str = ... # type: ignore
    USER_CREATED_DEAD_LETTER_QUEUE: str = ... # type: ignore
    USER_CREATED_DEAD_LETTER_QUEUE_ROUTING_KEY: str = ... # type: ignore
    USER_CREATED_RETRY_COUNT: int = ... # type: ignore

    FRONTEND_BASE_URL: str = ... # type: ignore

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    def logging_settings(self) -> LoggingSettings:
        return LoggingSettings(
            environment=self.ENVIRONMENT,
            service_name=self.SERVICE_NAME,
            log_level=self.LOG_LEVEL,
            log_format=self.LOG_FORMAT,
            log_retention_days=self.LOG_RETENTION_DAYS,
            log_directory=Path.joinpath(BASE_DIR, "..", "bin", "logs"),
        )


settings = Settings()
