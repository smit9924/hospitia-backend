from datetime import timedelta
from os import path
from pathlib import Path

from pika.exchange_type import ExchangeType
from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from auth.schemas.logging_schemas import LoggingSettings
from auth.types.enums import EnvironmentName, LogFormatName, LogLevelName

BASE_DIR: Path = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file = path.join(BASE_DIR, "../", ".env"),
        env_ignore_empty = True,
        extra = "ignore",
    )

    app_name: str = "Awesome API"

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
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = ... # type: ignore
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = ... # type: ignore
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES_REMEMBER_ME: int = ... # type: ignore

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

    # Notification topology
    EMAIL_NOTIFICATION_EXCHANGE: str = ... # type: ignore
    EMAIL_NOTIFICATION_EXCHANGE_TYPE: ExchangeType = ... # type: ignore
    FORGOT_PASSWORD_EMAIL_QUEUE: str = ... # type: ignore
    FORGOT_PASSWORD_EMAIL_QUEUE_ROUTING_KEY: str = ... # type: ignore
    VERIFY_EMAIL_OTP_EMAIL_QUEUE: str = ... # type: ignore
    VERIFY_EMAIL_OTP_EMAIL_QUEUE_ROUTING_KEY: str = ... # type: ignore

    # User events topology (Auth declares subscriber queues so events persist if those services are down)
    USER_EVENTS_EXCHANGE: str = ... # type: ignore
    USER_EVENTS_EXCHANGE_TYPE: ExchangeType = ... # type: ignore
    USER_CREATED_EVENT_TYPE: str = ... # type: ignore
    USER_CREATED_ROUTING_KEY: str = ... # type: ignore
    BOOKING_USER_CREATED_QUEUE: str = ... # type: ignore
    BOOKING_USER_CREATED_QUEUE_ROUTING_KEY: str = ... # type: ignore
    PAYMENT_USER_CREATED_QUEUE: str = ... # type: ignore
    PAYMENT_USER_CREATED_QUEUE_ROUTING_KEY: str = ... # type: ignore
    DASHBOARD_USER_CREATED_QUEUE: str = ... # type: ignore
    DASHBOARD_USER_CREATED_QUEUE_ROUTING_KEY: str = ... # type: ignore

    FRONTEND_BASE_URL: str = ... # type: ignore

    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = ... # type: ignore
    VERIFY_EMAIL_OTP_TIMEOUT: int = ... # type: ignore

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

    @computed_field
    @property
    def JWT_ACCESS_TOKEN_EXPIRE_MINUTES_TIMEDELTA(self) -> timedelta:
        """
        Return a timedelta representing the JWT access token lifetime.

        description
        -----------
            Compute and return a `timedelta` object based on the
            `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` setting.

        parameters
        ----------
        None

        Returns
        -------
        timedelta
            Time duration for which a JWT access token remains valid.
        """
        return timedelta(minutes=self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    @computed_field
    @property
    def JWT_REFRESH_TOKEN_EXPIRE_MINUTES_TIMEDELTA(self) -> timedelta:
        """
        Return a timedelta representing the JWT refresh token lifetime.

        description
        -----------
            Compute and return a `timedelta` object based on the
            `JWT_REFRESH_TOKEN_EXPIRE_MINUTES` setting.

        parameters
        ----------
        None

        Returns
        -------
        timedelta
            Time duration for which a JWT refresh token remains valid.
        """
        return timedelta(minutes=self.JWT_REFRESH_TOKEN_EXPIRE_MINUTES)

    @computed_field
    @property
    def JWT_REFRESH_TOKEN_EXPIRE_MINUTES_REMEMBER_ME_TIMEDELTA(self) -> timedelta:
        """
        Return a timedelta representing the JWT refresh token lifetime for remember-me sessions.

        description
        -----------
            Compute and return a `timedelta` object based on the
            `JWT_REFRESH_TOKEN_EXPIRE_MINUTES_REMEMBER_ME` setting.

        parameters
        ----------
        None

        Returns
        -------
        timedelta
            Time duration for which a JWT refresh token remains valid.
        """
        return timedelta(minutes=self.JWT_REFRESH_TOKEN_EXPIRE_MINUTES_REMEMBER_ME)

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
