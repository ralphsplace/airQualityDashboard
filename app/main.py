import time
import threading
import requests
import json
import os
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .database import engine, Base, get_db
from .models import AirReading
from .config import settings  # Import settings

# --- Configuration Access ---
POLL_URL = settings.poll_url
POLL_INTERVAL = settings.poll_interval

# --- App Initialization ---
app = FastAPI(
    title="Air Quality Monitor",
    description="Polls stations and provides API access to data.",
    version="1.0.0"
)

# Create DB tables on startup
Base.metadata.create_all(bind=engine)

# --- Background Polling Logic ---

def parse_and_store_data(data: dict, db: Session):
    """Parses the JSON payload and stores it in the DB."""
    try:
        # Extract fields based on the JSON structure provided
        station_id = data.get("station", {}).get("id")
        readings = data.get("readings", {})
        location = data.get("station", {}).get("location", {})

        # Create the DB record
        new_reading = AirReading(
            timestamp_utc=datetime.utcnow(), # Or use data timestamp if available
            station_id=station_id,
            pm1=readings.get("pm1"),
            pm25=readings.get("pm25"),
            pm10=readings.get("pm10"),
            temperature_c=readings.get("temperature"),
            humidity_pct=readings.get("humidity"),
            lat=location.get("latitude"),
            lon=location.get("longitude"),
            source_json=json.dumps(data)
        )
        
        db.add(new_reading)
        db.commit()
        print(f"[Poller] Saved reading for station: {station_id}")
        
    except Exception as e:
        print(f"[Poller] Error parsing data: {e}")
        db.rollback()

def poller_loop():
    """The infinite loop that polls the URL."""
    print(f"[Poller] Starting polling service. Target: {POLL_URL}")
    while True:
        try:
            response = requests.get(POLL_URL, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # We need a local DB session for this thread
                db = next(get_db())
                parse_and_store_data(data, db)
            else:
                print(f"[Poller] Received status {response.status_code}")
        except Exception as e:
            print(f"[Poller] Request failed: {e}")
        
        time.sleep(POLL_INTERVAL)

# Start the poller in a separate thread when the app starts
@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=poller_loop, daemon=True)
    thread.start()

# --- API Endpoints ---

@app.get("/", tags=["System"])
def read_root():
    return {"status": "running", "poller_target": POLL_URL}

@app.get("/status/current", tags=["Data"])
def get_current_status(db: Session = Depends(get_db)):
    """Returns the most recent reading recorded."""
    reading = db.query(AirReading).order_by(AirReading.timestamp_utc.desc()).first()
    if not reading:
        raise HTTPException(status_code=404, detail="No readings found")
    return reading

@app.get("/status/history", tags=["Data"])
def get_history(
    station_id: Optional[str] = None,
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """Returns historic readings."""
    query = db.query(AirReading).order_by(AirReading.timestamp_utc.desc())
    
    if station_id:
        query = query.filter(AirReading.station_id == station_id)
        
    results = query.limit(limit).all()
    return results
