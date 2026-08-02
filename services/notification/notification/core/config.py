from pathlib import Path

from pika.exchange_type import ExchangeType
from pydantic_settings import BaseSettings, SettingsConfigDict

SERVICE_ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=SERVICE_ROOT / ".env",
        env_ignore_empty = True,
        case_sensitive = False,
    )

    MQ_CLIENT_TYPE: str = ... # type: ignore

    # RabbitMQ
    RABBITMQ_HOST: str = ...  # type: ignore
    RABBITMQ_PORT: int = ...  # type: ignore
    RABBITMQ_USERNAME: str = ...  # type: ignore
    RABBITMQ_PASSWORD: str = ...  # type: ignore
    RABBITMQ_HEART_BEAT: int = ...  # type: ignore
    RABBITMQ_CONNECTION_TIMEOUT: int = ...  # type: ignore
    RABBITMQ_RETRY_ATTEMPTS: int = ...  # type: ignore
    RABBITMQ_RETRY_DELAY: int = ...  # type: ignore
    RABBITMQ_PUBLISH_RETRY_ATTEMPTS: int = ...  # type: ignore
    RABBITMQ_PUBLISH_RETRY_DELAY: int = ...  # type: ignore
    RABBITMQ_CONSUMER_RETRY_DELAY: int = ...  # type: ignore
    RABBITMQ_CONSUMER_PREFETCH_COUNT: int = ...  # type: ignore

    # Notification topology
    EMAIL_NOTIFICATION_EXCHANGE: str = ... # type: ignore
    EMAIL_NOTIFICATION_EXCHANGE_TYPE: ExchangeType = ... # type: ignore
    FORGOT_PASSWORD_EMAIL_QUEUE: str = ... # type: ignore
    FORGOT_PASSWORD_EMAIL_QUEUE_ROUTING_KEY: str = ... # type: ignore

    # Email (SMTP)
    SMTP_HOST: str = ... # type: ignore
    SMTP_PORT: int = ... # type: ignore
    SMTP_USERNAME: str = ... # type: ignore
    SMTP_PASSWORD: str = ... # type: ignore
    SMTP_FROM: str = ... # type: ignore
    SMTP_USE_TLS: bool = ... # type: ignore

settings = Settings()
