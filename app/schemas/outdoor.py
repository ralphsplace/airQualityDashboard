from __future__ import annotations

from datetime import datetime

from app.schemas.common import ApiBaseModel


class OutdoorCurrentResponse(ApiBaseModel):
    recorded_at_utc: datetime
    source_time_utc: datetime | None = None
    aqi: float | None = None
    dominant_pollutant: str | None = None
    city_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    co: float | None = None
    h: float | None = None
    no2: float | None = None
    o3: float | None = None
    p: float | None = None
    pm25: float | None = None
    so2: float | None = None
    t: float | None = None
    w: float | None = None


class OutdoorHistoryItem(ApiBaseModel):
    recorded_at_utc: datetime
    source_time_utc: datetime | None = None
    aqi: float | None = None
    dominant_pollutant: str | None = None
    city_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    co: float | None = None
    h: float | None = None
    no2: float | None = None
    o3: float | None = None
    p: float | None = None
    pm25: float | None = None
    so2: float | None = None
    t: float | None = None
    w: float | None = None


class OutdoorHistoryResponse(ApiBaseModel):
    from_utc: datetime
    to_utc: datetime
    items: list[OutdoorHistoryItem]
