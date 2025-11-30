from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from os import path
from pydantic import PostgresDsn, computed_field

BASE_DIR: Path = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file = path.join(BASE_DIR, "../", ".env"),
        env_ignore_empty = True,
        extra = "ignore",
    )

    app_name: str = "Awesome API"


    # Postgres
    # Ignore Pylance type checks here. These fields are populated by Pydantic Settings at runtime,
    # and the application should fail loudly if any required environment variable is missing.
    POSTGRES_SERVER: str = ... # type: ignore
    POSTGRES_PORT: int = ... # type: ignore
    POSTGRES_DB: str = ... # type: ignore
    POSTGRES_USER: str = ... # type: ignore
    POSTGRES_PASSWORD: str = ... # type: ignore

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

settings = Settings()