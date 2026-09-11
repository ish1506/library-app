from functools import lru_cache
from pathlib import Path
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    configured_database_url: str | None = Field(
        default=None, validation_alias="DATABASE_URL"
    )
    postgres_db: str | None = Field(default=None, validation_alias="POSTGRES_DB")
    postgres_user: str | None = Field(default=None, validation_alias="POSTGRES_USER")
    postgres_password: str | None = Field(
        default=None, validation_alias="POSTGRES_PASSWORD"
    )
    jwt_secret_key: str = Field(validation_alias="JWT_SECRET_KEY")
    cors_allowed_origins: str = Field(
        default="", validation_alias="CORS_ALLOWED_ORIGINS"
    )

    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    @model_validator(mode="after")
    def validate_database_configuration(self) -> Self:
        if self.configured_database_url is not None:
            return self
        if all((self.postgres_db, self.postgres_user, self.postgres_password)):
            return self
        raise ValueError(
            "Set DATABASE_URL or POSTGRES_DB, POSTGRES_USER, and POSTGRES_PASSWORD"
        )

    @property
    def database_url(self) -> str:
        if self.configured_database_url is not None:
            return self.configured_database_url
        assert self.postgres_db is not None
        assert self.postgres_user is not None
        assert self.postgres_password is not None
        return URL.create(
            "postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password,
            host="localhost",
            port=5432,
            database=self.postgres_db,
        ).render_as_string(hide_password=False)

    @property
    def allowed_cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue]


settings = get_settings()
