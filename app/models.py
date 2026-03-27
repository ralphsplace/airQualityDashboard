from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import func
from .database import Base

class AirReading(Base):
    __tablename__ = "air_readings"

    id = Column(Integer, primary_key=True, index=True)
    timestamp_utc = Column(DateTime, default=func.now(), index=True)
    station_id = Column(String, index=True)
    pm1 = Column(Float)
    pm25 = Column(Float)
    pm10 = Column(Float)
    temperature_c = Column(Float)
    humidity_pct = Column(Float)
    lat = Column(Float)
    lon = Column(Float)
    source_json = Column(String)

class WaqiReading(Base):
    __tablename__ = "waqi_readings"

    id = Column(Integer, primary_key=True, index=True)
    timestamp_utc = Column(DateTime, default=func.now(), index=True)

    waqi_status = Column(String)
    aqi = Column(Integer)
    dominant_pollutant = Column(String)

    station_name = Column(String, index=True)
    station_uid = Column(Integer, index=True)
    station_lat = Column(Float)
    station_lon = Column(Float)
    station_url = Column(String)
    measurement_time = Column(String)

    pm25 = Column(Float)
    pm10 = Column(Float)
    no2 = Column(Float)
    o3 = Column(Float)
    so2 = Column(Float)
    co = Column(Float)
    t = Column(Float)
    h = Column(Float)
    p = Column(Float)
    w = Column(Float)

    source_json = Column(String)

class WaqiForecast(Base):
    __tablename__ = "waqi_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    fetched_at_utc = Column(DateTime, default=func.now(), index=True)

    station_uid = Column(Integer, index=True)
    station_name = Column(String, index=True)

    forecast_date = Column(String, index=True)   # e.g. "2026-03-27"
    pollutant = Column(String, index=True)       # pm25, pm10, o3, etc.

    avg = Column(Float)
    min = Column(Float)
    max = Column(Float)

    source_json = Column(String)