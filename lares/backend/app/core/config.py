from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://lares:lares@localhost:5432/lares"
    lares_web_origin: str = "http://localhost:5183"

    entsoe_api_token: str | None = None
    google_maps_api_key: str | None = None
    opencorporates_api_token: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
