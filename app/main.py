from pathlib import Path
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.orm import Session

from .database import engine, Base, get_db
from .models import AirReading
from .config import settings

import json
import threading
import time

import requests
import uvicorn


# --- Configuration Access ---
GAIA_A08_URL = settings.gaia_a08_url
GAIA_A08_POLL_INTERVAL = getattr(settings, "gaia_a08_poll_interval", 60)


# --- App Initialization ---
app = FastAPI(
    title="Air Quality Monitor",
    description="Polls stations and provides API access to data.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|192\.168\.53\.\d{1,3}|[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.(local|home))(:\d+)?$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_private_network=True,
)


app.mount("/static", StaticFiles(directory=str("/dist")), name="static")


# Create DB tables on startup
Base.metadata.create_all(bind=engine)


@contextmanager
def db_session():
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


# --- Background Polling Logic ---
def parse_and_store_data(data: dict, db: Session):
    """Parses the JSON payload and stores it in the DB."""
    try:
        station_id = data.get("station", {}).get("id")
        readings = data.get("readings", {})
        location = data.get("station", {}).get("location", {})

        new_reading = AirReading(
            timestamp_utc=datetime.utcnow(),
            station_id=station_id,
            pm1=readings.get("pm1"),
            pm25=readings.get("pm25"),
            pm10=readings.get("pm10"),
            temperature_c=readings.get("temperature"),
            humidity_pct=readings.get("humidity"),
            lat=location.get("latitude"),
            lon=location.get("longitude"),
            source_json=json.dumps(data),
        )

        db.add(new_reading)
        db.commit()
        print(f"[Poller] Saved reading for station: {station_id}")

    except Exception as e:
        db.rollback()
        print(f"[Poller] Error parsing data: {e}")


def poller_loop():
    """The infinite loop that polls the URL."""
    print(f"[Poller] Starting polling service. Target: {GAIA_A08_URL}")

    while True:
        try:
            response = requests.get(GAIA_A08_URL, timeout=10)
            if response.status_code == 200:
                data = response.json()
                with db_session() as db:
                    parse_and_store_data(data, db)
            else:
                print(f"[Poller] Received status {response.status_code}")
        except Exception as e:
            print(f"[Poller] Request failed: {e}")

        time.sleep(GAIA_A08_POLL_INTERVAL)


# Start the poller in a separate thread when the app starts
@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=poller_loop, daemon=True)
    thread.start()


# --- Static Page Routes ---
@app.get("/", include_in_schema=False)
def serve_index():
    index_file = "/dist/index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse(status_code=404, content={"detail": "index.html not found"})


@app.get("/favicon.svg", include_in_schema=False)
def serve_favicon():
    favicon = "/dist/img/favicon.svg"
    if favicon.exists():
        return FileResponse(favicon)
    return JSONResponse(status_code=404, content={"detail": "favicon not found"})


# --- API Endpoints ---
@app.get("/health", tags=["System"])
def health_check(db: Session = Depends(get_db)):
    """Check database connection and basic health."""
    try:
        db.query(AirReading).limit(1).all()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "error", "error": str(e)}


@app.get("/status/current", tags=["Data"])
def get_current_status(
    station_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Returns the most recent reading recorded."""
    try:
        query = db.query(AirReading).order_by(AirReading.timestamp_utc.desc())

        if station_id:
            query = query.filter(AirReading.station_id == station_id)

        reading = query.first()
        if not reading:
            raise HTTPException(status_code=404, detail="No readings found")
        return reading
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Error] get_current_status failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/status/history", tags=["Data"])
def get_history(
    station_id: Optional[str] = None,
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
):
    """Returns historic readings."""
    query = db.query(AirReading).order_by(AirReading.timestamp_utc.desc())

    if station_id:
        query = query.filter(AirReading.station_id == station_id)

    return query.limit(limit).all()


@app.get("/devices", tags=["Data"])
def list_devices(db: Session = Depends(get_db)):
    rows = (
        db.query(
            AirReading.station_id,
            func.max(AirReading.timestamp_utc).label("last_seen"),
            func.max(AirReading.lat).label("lat"),
            func.max(AirReading.lon).label("lon"),
        )
        .group_by(AirReading.station_id)
        .order_by(AirReading.station_id.asc())
        .all()
    )

    return [
        {
            "station_id": row.station_id,
            "name": row.station_id,
            "last_seen": row.last_seen.isoformat() if row.last_seen else None,
            "lat": row.lat,
            "lon": row.lon,
        }
        for row in rows
    ]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008, reload=True)