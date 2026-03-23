from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import func
from .database import Base

class AirReading(Base):
    __tablename__ = "air_readings"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Required Fields
    timestamp_utc = Column(DateTime, default=func.now())
    station_id = Column(String, index=True)
    
    pm1 = Column(Float)
    pm25 = Column(Float)
    pm10 = Column(Float)
    
    temperature_c = Column(Float)
    humidity_pct = Column(Float)
    
    lat = Column(Float)
    lon = Column(Float)
    
    # Store the raw JSON for debugging/future use
    source_json = Column(String)
