from __future__ import annotations

from dataclasses import dataclass
import os


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Air Pollution Monitor API")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://airpollution:airpollution@postgres:5432/airpollution",
    )
    indoor_source_url: str = os.getenv(
        "INDOOR_SOURCE_URL",
        "http://192.168.53.203/realtime",
    )
    waqi_base_url: str = os.getenv(
        "WAQI_URL",
        "https://api.waqi.info/feed/here/",
    )
    waqi_token: str = os.getenv("WAQI_TOKEN", "")
    poll_interval_seconds: int = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))
    request_timeout_seconds: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))
    enable_poller: bool = _bool_env("ENABLE_POLLER", True)
    history_default_days: int = int(os.getenv("HISTORY_DEFAULT_DAYS", "7"))
    history_max_days: int = int(os.getenv("HISTORY_MAX_DAYS", "30"))


settings = Settings()
