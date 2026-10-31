from __future__ import annotations

import os
import secrets
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
STATIC_DIR = BACKEND_DIR / "static"

MODEL_NAME = "VietTung04/vit-l-16-food-classifier"
MODEL_DIR = BACKEND_DIR / "models" / "vietnamese_food_classifier"
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.60"))
TOP_K = int(os.getenv("TOP_K", "3"))
MAX_IMAGE_BYTES = int(os.getenv("MAX_IMAGE_BYTES", str(10 * 1024 * 1024)))
MAX_IMAGE_PIXELS = int(os.getenv("MAX_IMAGE_PIXELS", str(40_000_000)))
MODEL_LOAD_ON_STARTUP = os.getenv("MODEL_LOAD_ON_STARTUP", "true").lower() not in {
    "0",
    "false",
    "no",
}

SUPPORTED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png"}

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{(DATA_DIR / 'vi_viet.db').as_posix()}",
)


def _resolve_auth_secret(environment: str, configured_secret: str | None) -> str:
    """Return a safe JWT secret and refuse unsafe production startup.

    Development uses an ephemeral secret when none is configured. This keeps a
    fresh checkout safe by default, at the cost of invalidating local sessions
    whenever the backend process restarts.
    """

    is_production = environment.strip().casefold() in {"prod", "production"}
    if configured_secret is None or not configured_secret.strip():
        if is_production:
            raise RuntimeError("AUTH_SECRET_KEY is required when APP_ENV=production.")
        return secrets.token_urlsafe(48)
    if is_production and len(configured_secret.encode("utf-8")) < 32:
        raise RuntimeError("AUTH_SECRET_KEY must be at least 32 bytes in production.")
    return configured_secret


APP_ENV = os.getenv("APP_ENV", "development")
AUTH_SECRET_KEY = _resolve_auth_secret(APP_ENV, os.getenv("AUTH_SECRET_KEY"))
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "30"))
REFRESH_TOKEN_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", "30"))
AUTH_RATE_LIMIT_PER_MINUTE = int(os.getenv("AUTH_RATE_LIMIT_PER_MINUTE", "60"))
PREDICT_RATE_LIMIT_PER_MINUTE = int(os.getenv("PREDICT_RATE_LIMIT_PER_MINUTE", "30"))
CORS_ORIGINS = tuple(
    item.strip()
    for item in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:8080,http://127.0.0.1:8080",
    ).split(",")
    if item.strip()
)
