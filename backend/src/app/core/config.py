from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DIO_", extra="ignore")

    app_name: str = "diopside"
    app_version: str = "0.1.0"
    debug: bool = False
    contract_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[3] / "data" / "public"
    )
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)
    youtube_api_key: str | None = Field(default=None, repr=False)
    youtube_api_base_url: str = "https://www.googleapis.com/youtube/v3"


@lru_cache
def get_settings() -> Settings:
    return Settings()
