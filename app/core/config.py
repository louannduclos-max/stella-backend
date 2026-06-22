import os
from functools import lru_cache
from pydantic import BaseModel


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseModel):
    app_name: str = "Stella - Contracts & KPI Core"
    app_version: str = "1.7.0"
    environment: str = "local"
    google_places_api_key: str | None = os.environ.get("GOOGLE_PLACES_API_KEY")
    stella_storage_dir: str | None = os.environ.get("STELLA_STORAGE_DIR")
    # Front -> Backend : Bearer token verifie sur POST /generate-study
    webhook_secret: str | None = os.environ.get("WEBHOOK_SECRET")
    # Backend -> Front : callback POST /api/public/generation-webhook
    front_webhook_url: str | None = os.environ.get("FRONT_WEBHOOK_URL")
    generation_webhook_secret: str | None = os.environ.get("GENERATION_WEBHOOK_SECRET")
    cors_allow_origins: list[str] = _split_csv(
        os.environ.get("CORS_ALLOW_ORIGINS")
    ) or [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://lovable.dev",
        "https://*.lovable.app",
        "https://*.lovableproject.com",
    ]
    cors_allow_origin_regex: str | None = os.environ.get(
        "CORS_ALLOW_ORIGIN_REGEX",
        r"https://.*\.(lovable\.app|lovableproject\.com)$",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
