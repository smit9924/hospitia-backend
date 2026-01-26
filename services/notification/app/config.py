from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".devcontainer/.env",
        case_sensitive=False,
    )

    # RabbitMQ connection
    rabbitmq_host: str
    rabbitmq_port: int = 5672
    rabbitmq_username: str
    rabbitmq_password: str

    # Notification topology
    notification_exchange: str
    notification_exchange_type: str = "direct"
    max_priority: int = 10
    email_queue: str
    email_routing_key: str


settings = Settings()
