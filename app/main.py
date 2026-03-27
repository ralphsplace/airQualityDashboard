from __future__ import annotations

import json
import os
import re
import threading
import time
from datetime import datetime, timedelta, timezone
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
from .models import AirReading, WaqiReading

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

POLL_URL = settings.gaia_a08_url
POLL_INTERVAL = max(5, int(settings.gaia_a08_poll_interval))
BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "dist"
ASSETS_DIR = DIST_DIR / "assets"

WAQI_ENABLED = getattr(settings, "waqi_enabled", False)
WAQI_URL = getattr(settings, "waqi_url", "https://api.waqi.info/feed/here/")
WAQI_TOKEN = getattr(settings, "waqi_token", "")
WAQI_POLL_INTERVAL = getattr(settings, "waqi_poll_interval", 300)

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
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    query = db.query(AirReading).filter(AirReading.timestamp_utc >= seven_days_ago)
    if station_id:
        query = query.filter(AirReading.station_id == station_id)
    return query.order_by(AirReading.timestamp_utc.desc()).limit(limit).all()


@app.post("/poll/once", tags=["System"])
def poll_once_endpoint(db: Session = Depends(get_db)):
    reading = poll_once(db)
    return {"saved": True, "station_id": reading.station_id, "timestamp_utc": reading.timestamp_utc}


@app.get("/waqi/current", tags=["Data"])
def get_waqi_current(db: Session = Depends(get_db)):
    reading = db.query(WaqiReading).order_by(WaqiReading.timestamp_utc.desc()).first()
    if not reading:
        raise HTTPException(status_code=404, detail="No WAQI readings found")
    return reading

@app.get("/waqi/history", tags=["Data"])
def get_waqi_history(limit: int = Query(100, le=1000), db: Session = Depends(get_db)):
    return (
        db.query(WaqiReading)
        .order_by(WaqiReading.timestamp_utc.desc())
        .limit(limit)
        .all()
    )

@app.get("/waqi/status", tags=["Data"])
def get_waqi_status(db: Session = Depends(get_db)):
    latest = db.query(WaqiReading).order_by(WaqiReading.timestamp_utc.desc()).first()
    return {
        "enabled": WAQI_ENABLED,
        "poll_interval": WAQI_POLL_INTERVAL,
        "has_token": bool(WAQI_TOKEN),
        "latest_timestamp": latest.timestamp_utc.isoformat() if latest else None,
        "latest_station": latest.station_name if latest else None,
    }

def parse_waqi_value(node):
    if isinstance(node, dict):
        return node.get("v")
    return None

def parse_and_store_waqi(data: dict, db: Session):
    try:
        status = data.get("status")
        payload = data.get("data", {})

        if status != "ok":
            print(f"[WAQI] API status not ok: {status}")
            return

        city = payload.get("city", {}) or {}
        iaqi = payload.get("iaqi", {}) or {}
        time_data = payload.get("time", {}) or {}

        geo = city.get("geo", [None, None])
        lat = geo[0] if isinstance(geo, list) and len(geo) > 0 else None
        lon = geo[1] if isinstance(geo, list) and len(geo) > 1 else None

        new_reading = WaqiReading(
            timestamp_utc=datetime.utcnow(),
            waqi_status=status,
            aqi=payload.get("aqi"),
            dominant_pollutant=payload.get("dominentpol"),
            station_name=city.get("name"),
            station_uid=idx if (idx := payload.get("idx")) else None,
            station_lat=lat,
            station_lon=lon,
            station_url=city.get("url"),
            measurement_time=time_data.get("s"),
            pm25=parse_waqi_value(iaqi.get("pm25")),
            pm10=parse_waqi_value(iaqi.get("pm10")),
            no2=parse_waqi_value(iaqi.get("no2")),
            o3=parse_waqi_value(iaqi.get("o3")),
            so2=parse_waqi_value(iaqi.get("so2")),
            co=parse_waqi_value(iaqi.get("co")),
            t=parse_waqi_value(iaqi.get("t")),
            h=parse_waqi_value(iaqi.get("h")),
            p=parse_waqi_value(iaqi.get("p")),
            w=parse_waqi_value(iaqi.get("w")),
            source_json=json.dumps(data),
        )
        db.add(new_reading)
        db.commit()
        print(f"[WAQI] Saved reading for station: {new_reading.station_name}")
    except Exception as e:
        db.rollback()
        print(f"[WAQI] Error parsing data: {e}")

def parse_and_store_waqi_forecast(data: dict, db: Session):
    try:
        if data.get("status") != "ok":
            return

        payload = data.get("data", {}) or {}
        city = payload.get("city", {}) or {}
        forecast = payload.get("forecast", {}) or {}
        daily = forecast.get("daily", {}) or {}

        station_uid = payload.get("idx")
        station_name = city.get("name")

        # Optional cleanup strategy:
        # remove older forecast rows for this station before inserting refreshed data
        if station_uid:
            db.query(WaqiForecast).filter(
                WaqiForecast.station_uid == station_uid
            ).delete()

        for pollutant, entries in daily.items():
            if not isinstance(entries, list):
                continue

            for entry in entries:
                row = WaqiForecast(
                    fetched_at_utc=datetime.utcnow(),
                    station_uid=station_uid,
                    station_name=station_name,
                    forecast_date=entry.get("day"),
                    pollutant=pollutant,
                    avg=entry.get("avg"),
                    min=entry.get("min"),
                    max=entry.get("max"),
                    source_json=json.dumps(entry),
                )
                db.add(row)

        db.commit()
        print(f"[WAQI] Saved forecast rows for station: {station_name}")

    except Exception as e:
        db.rollback()
        print(f"[WAQI] Forecast parse error: {e}")

@app.get("/waqi/forecast", tags=["Data"])
def get_waqi_forecast(db: Session = Depends(get_db)):
    rows = (
        db.query(WaqiForecast)
        .order_by(WaqiForecast.forecast_date.asc(), WaqiForecast.pollutant.asc())
        .all()
    )
    return rows

@app.get("/waqi/forecast/{pollutant}", tags=["Data"])
def get_waqi_forecast_by_pollutant(pollutant: str, db: Session = Depends(get_db)):
    rows = (
        db.query(WaqiForecast)
        .filter(WaqiForecast.pollutant == pollutant.lower())
        .order_by(WaqiForecast.forecast_date.asc())
        .all()
    )
    return rows

@app.get("/waqi/forecast/summary", tags=["Data"])
def get_waqi_forecast_summary(db: Session = Depends(get_db)):
    rows = (
        db.query(WaqiForecast)
        .order_by(WaqiForecast.forecast_date.asc(), WaqiForecast.pollutant.asc())
        .all()
    )

    result = {}
    for row in rows:
        day = row.forecast_date
        if day not in result:
            result[day] = {}

        result[day][row.pollutant] = {
            "avg": row.avg,
            "min": row.min,
            "max": row.max,
            "station_name": row.station_name,
            "station_uid": row.station_uid,
        }

    return result        


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

def waqi_poller_loop():
    if not WAQI_ENABLED:
        print("[WAQI] Poller disabled")
        return

    if not WAQI_TOKEN:
        print("[WAQI] Missing token, poller not started")
        return

    print(f"[WAQI] Starting polling service. Target: {WAQI_URL}")
    while True:
        db = SessionLocal()
        try:
            response = requests.get(
                WAQI_URL,
                params={"token": WAQI_TOKEN},
                timeout=15,
            )
            if response.status_code == 200:
                data = response.json()
                parse_and_store_waqi(data, db)
            else:
                print(f"[WAQI] Received status {response.status_code}")
        except Exception as e:
            print(f"[WAQI] Request failed: {e}")

        time.sleep(WAQI_POLL_INTERVAL)

@app.on_event("startup")
def startup_event():
    gaia_thread = threading.Thread(target=poller_loop, daemon=True)
    gaia_thread.start()

    if WAQI_ENABLED:
        waqi_thread = threading.Thread(target=waqi_poller_loop, daemon=True)
        waqi_thread.start()