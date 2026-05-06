from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

SERVICE_ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=SERVICE_ROOT / ".env",
        env_ignore_empty = True,
        case_sensitive = False,
    )

    # RabbitMQ connection
    rabbitmq_host: str = ... # type: ignore
    rabbitmq_port: int = ... # type: ignore
    rabbitmq_username: str = ... # type: ignore
    rabbitmq_password: str = ... # type: ignore

    # Notification topology
    notification_exchange: str = ... # type: ignore
    notification_exchange_type: str = "direct"
    max_priority: int = 10
    email_queue: str = ... # type: ignore
    email_routing_key: str = "email.send"

    # Email (SMTP)
    smtp_host: str = ... # type: ignore
    smtp_port: int = 587
    smtp_username: str = ... # type: ignore
    smtp_password: str = ... # type: ignore
    smtp_from: str = ... # type: ignore
    smtp_use_tls: bool = True

settings = Settings()
