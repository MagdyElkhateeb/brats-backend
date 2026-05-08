from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/brats_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-this-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    MODEL_ENDPOINT_URL: str = "http://16.171.169.120:8000/predict/"
    MODEL_REQUEST_TIMEOUT_SECONDS: int = 1800
    STORAGE_ROOT: str = "storage"
    JWT_ALGORITHM: str = Field(default="HS256", exclude=True)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
