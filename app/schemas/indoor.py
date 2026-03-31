from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ApiBaseModel


class IndoorCurrentResponse(ApiBaseModel):
    recorded_at_utc: datetime
    source_id: str
    latitude: float | None = None
    longitude: float | None = None
    pm1: float | None = None
    pm25: float | None = None
    pm10: float | None = None
    temperature_c: float | None = None
    humidity_pct: float | None = None


class IndoorHistoryItem(ApiBaseModel):
    recorded_at_utc: datetime
    pm1: float | None = None
    pm25: float | None = None
    pm10: float | None = None
    temperature_c: float | None = None
    humidity_pct: float | None = None


class IndoorHistoryResponse(ApiBaseModel):
    source_id: str | None = None
    from_utc: datetime
    to_utc: datetime
    items: list[IndoorHistoryItem]
