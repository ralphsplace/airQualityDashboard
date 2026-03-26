from __future__ import annotations

import json
import os
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, engine, get_db, SessionLocal
from .models import AirReading

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Air Quality Monitor",
    description="Polls air quality stations, stores readings, and serves a bundled dashboard.",
    version="1.1.0",
)

# Same-origin serving is the real cure for most CORS heartburn.
# This still keeps local development pleasant across RFC1918 ranges.
LOCAL_NAT_REGEX = (
    r"^https?://("
    r"localhost|127(?:\.\d{1,3}){3}|0\.0\.0\.0|"
    r"10(?:\.\d{1,3}){3}|"
    r"192\.168(?:\.\d{1,3}){2}|"
    r"172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2}"
    r")(?::\d{1,5})?$"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["null"],
    allow_origin_regex=LOCAL_NAT_REGEX,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

POLL_URL = settings.poll_url
POLL_INTERVAL = max(5, int(settings.poll_interval))
BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "dist"
ASSETS_DIR = DIST_DIR / "assets"


@app.get("/health", tags=["System"])
def health():
    return {
        "status": "ok",
        "poll_url": POLL_URL,
        "poll_interval": POLL_INTERVAL,
        "ui_available": DIST_DIR.exists(),
    }


@app.get("/", include_in_schema=False)
def root_index():
    index_file = DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "status": "running",
        "message": "Backend is up. UI build not found. Build the frontend or use the included dist folder.",
        "openapi": "/docs",
    }


if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

favicon_candidates = [DIST_DIR / "favicon.ico", BASE_DIR / "public" / "favicon.ico"]


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    for candidate in favicon_candidates:
        if candidate.exists():
            return FileResponse(candidate)
    raise HTTPException(status_code=404, detail="favicon not found")


@app.get("/api", tags=["System"])
def api_root():
    return {"status": "running", "poller_target": POLL_URL, "docs": "/docs"}


@app.get("/devices", tags=["Data"])
def get_devices(db: Session = Depends(get_db)):
    rows = (
        db.query(AirReading.station_id)
        .filter(AirReading.station_id.isnot(None))
        .distinct()
        .order_by(AirReading.station_id.asc())
        .all()
    )
    return [{"station_id": station_id, "name": station_id} for (station_id,) in rows]


@app.get("/status/current", tags=["Data"])
def get_current_status(
    station_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(AirReading)
    if station_id:
        query = query.filter(AirReading.station_id == station_id)
    reading = query.order_by(AirReading.timestamp_utc.desc()).first()
    if not reading:
        raise HTTPException(status_code=404, detail="No readings found")
    return reading


@app.get("/status/history", tags=["Data"])
def get_history(
    station_id: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    query = db.query(AirReading)
    if station_id:
        query = query.filter(AirReading.station_id == station_id)
    return query.order_by(AirReading.timestamp_utc.desc()).limit(limit).all()


@app.post("/poll/once", tags=["System"])
def poll_once_endpoint(db: Session = Depends(get_db)):
    reading = poll_once(db)
    return {"saved": True, "station_id": reading.station_id, "timestamp_utc": reading.timestamp_utc}


@app.get("/{full_path:path}", include_in_schema=False)
def spa_fallback(full_path: str):
    if full_path.startswith("api") or full_path.startswith("status") or full_path.startswith("devices") or full_path.startswith("docs") or full_path.startswith("openapi") or full_path.startswith("redoc") or full_path.startswith("poll") or full_path.startswith("health"):
        raise HTTPException(status_code=404, detail="Not found")
    index_file = DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="Not found")



def parse_and_store_data(data: dict, db: Session) -> AirReading:
    station = data.get("station") or {}
    readings = data.get("readings") or {}
    location = station.get("location") or {}

    new_reading = AirReading(
        timestamp_utc=datetime.now(timezone.utc).replace(tzinfo=None),
        station_id=station.get("id"),
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
    db.refresh(new_reading)
    return new_reading



def poll_once(db: Session) -> AirReading:
    response = requests.get(POLL_URL, timeout=10)
    response.raise_for_status()
    data = response.json()
    return parse_and_store_data(data, db)



def poller_loop() -> None:
    print(f"[Poller] Starting polling service. Target: {POLL_URL}")
    while True:
        db = SessionLocal()
        try:
            reading = poll_once(db)
            print(f"[Poller] Saved reading for station: {reading.station_id}")
        except Exception as exc:
            db.rollback()
            print(f"[Poller] Request failed: {exc}")
        finally:
            db.close()
        time.sleep(POLL_INTERVAL)


@app.on_event("startup")
def startup_event() -> None:
    if os.environ.get("AIR_QUALITY_DISABLE_POLLER", "0") == "1":
        print("[Poller] Disabled via AIR_QUALITY_DISABLE_POLLER=1")
        return
    thread = threading.Thread(target=poller_loop, daemon=True)
    thread.start()
