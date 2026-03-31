from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base

JSONType = JSON().with_variant(JSONB(), "postgresql")


class IndoorReading(Base):
    __tablename__ = "indoor_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recorded_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    source_id: Mapped[str] = mapped_column(String(128), index=True)
    mac: Mapped[str | None] = mapped_column(String(128), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm1: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm25: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm10: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_json: Mapped[dict[str, Any]] = mapped_column(JSONType)


class OutdoorReading(Base):
    __tablename__ = "outdoor_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recorded_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    source_time_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    waqi_idx: Mapped[int | None] = mapped_column(Integer, nullable=True)
    city_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    aqi: Mapped[float | None] = mapped_column(Float, nullable=True)
    dominant_pollutant: Mapped[str | None] = mapped_column(String(64), nullable=True)
    co: Mapped[float | None] = mapped_column(Float, nullable=True)
    h: Mapped[float | None] = mapped_column(Float, nullable=True)
    no2: Mapped[float | None] = mapped_column(Float, nullable=True)
    o3: Mapped[float | None] = mapped_column(Float, nullable=True)
    p: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm25: Mapped[float | None] = mapped_column(Float, nullable=True)
    so2: Mapped[float | None] = mapped_column(Float, nullable=True)
    t: Mapped[float | None] = mapped_column(Float, nullable=True)
    w: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_json: Mapped[dict[str, Any]] = mapped_column(JSONType)

    forecasts: Mapped[list["OutdoorForecast"]] = relationship(
        back_populates="outdoor_reading",
        cascade="all, delete-orphan",
        order_by="OutdoorForecast.forecast_type, OutdoorForecast.forecast_day",
    )


class OutdoorForecast(Base):
    __tablename__ = "outdoor_forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    outdoor_reading_id: Mapped[int] = mapped_column(ForeignKey("outdoor_readings.id", ondelete="CASCADE"), index=True)
    forecast_type: Mapped[str] = mapped_column(String(64), index=True)
    forecast_day: Mapped[date] = mapped_column(Date, index=True)
    avg_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_json: Mapped[dict[str, Any]] = mapped_column(JSONType)

    outdoor_reading: Mapped[OutdoorReading] = relationship(back_populates="forecasts")
