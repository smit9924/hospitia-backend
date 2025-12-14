from datetime import timedelta
from os import path
from pathlib import Path

from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR: Path = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file = path.join(BASE_DIR, "../", ".env"),
        env_ignore_empty = True,
        extra = "ignore",
    )

    app_name: str = "Awesome API"


    API_V1_STR: str = "/api/v1"  # Base path for API version 1 endpoints


    # Ignore Pylance type checks here. These fields are populated by Pydantic Settings at runtime,
    # and the application should fail loudly if any required environment variable is missing.

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


settings = Settings()
