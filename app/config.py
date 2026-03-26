from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class Settings(BaseModel):
    poll_url: str = Field(default="http://127.0.0.1:8081/realtime")
    poll_interval: int = Field(default=60)
    database_type: str = Field(default="sqlite")
    sqlite_path: str = Field(default="./air_quality.db")


def _load_yaml() -> dict[str, Any]:
    root = Path(__file__).resolve().parent.parent
    config_path = root / "config.yaml"
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
        return data if isinstance(data, dict) else {}


raw = _load_yaml()
gaia = raw.get("gaia_a08", {}) if isinstance(raw.get("gaia_a08"), dict) else {}
database = raw.get("database", {}) if isinstance(raw.get("database"), dict) else {}

settings = Settings(
    poll_url=gaia.get("url", "http://127.0.0.1:8081/realtime"),
    poll_interval=int(gaia.get("poll_interval", 60)),
    database_type=str(database.get("type", "sqlite")),
    sqlite_path=str(database.get("sqlite_path", "./air_quality.db")),
)
