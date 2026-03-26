from __future__ import annotations

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class AirReading(Base):
    __tablename__ = "air_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp_utc: Mapped[object] = mapped_column(DateTime, nullable=False, index=True)
    station_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    pm1: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm25: Mapped[float | None] = mapped_column(Float, nullable=True)
    pm10: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_json: Mapped[str | None] = mapped_column(Text, nullable=True)
