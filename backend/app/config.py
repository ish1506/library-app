from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(validation_alias="DATABASE_URL")
    jwt_secret_key: str = Field(validation_alias="JWT_SECRET_KEY")
    reservation_hold_seconds: int = Field(
        default=86_400, gt=0, validation_alias="RESERVATION_HOLD_SECONDS"
    )
    reservation_worker_interval_seconds: int = Field(
        default=60, gt=0, validation_alias="RESERVATION_WORKER_INTERVAL_SECONDS"
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue]


settings = get_settings()
