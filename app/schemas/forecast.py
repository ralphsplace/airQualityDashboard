from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, field_serializer

from app.schemas.common import ApiBaseModel


class ForecastItem(BaseModel):
    day: date
    avg: float | None = None
    min: float | None = None
    max: float | None = None

    @field_serializer("day")
    def serialize_day(self, value: date) -> str:
        return value.isoformat()

class ForecastPollutant(BaseModel):
    pollutant: str
    avg: float | None = None
    min: float | None = None
    max: float | None = None

class OutdoorForecastCurrentResponse(ApiBaseModel):
    source_time_utc: datetime | None = None
    city_name: str | None = None
    forecast: dict[str, list[ForecastItem]]

class OutdoorForecastByDateResponse(ApiBaseModel):
    source_time_utc: datetime | None = None
    city_name: str | None = None
    forecast: dict[date, list[ForecastPollutant]]
