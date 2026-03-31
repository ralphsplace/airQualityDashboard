from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from app.core.time import parse_datetime_to_utc, utc_now


@dataclass(slots=True)
class IndoorMapped:
    source_id: str
    mac: str | None
    latitude: float | None
    longitude: float | None
    pm1: float | None
    pm25: float | None
    pm10: float | None
    temperature_c: float | None
    humidity_pct: float | None
    recorded_at_utc: object
    raw_json: dict[str, Any]


@dataclass(slots=True)
class OutdoorForecastMapped:
    forecast_type: str
    forecast_day: date
    avg_value: float | None
    min_value: float | None
    max_value: float | None
    raw_json: dict[str, Any]


@dataclass(slots=True)
class OutdoorMapped:
    recorded_at_utc: object
    source_time_utc: object | None
    waqi_idx: int | None
    city_name: str | None
    latitude: float | None
    longitude: float | None
    aqi: float | None
    dominant_pollutant: str | None
    co: float | None
    h: float | None
    no2: float | None
    o3: float | None
    p: float | None
    pm25: float | None
    so2: float | None
    t: float | None
    w: float | None
    raw_json: dict[str, Any]
    forecasts: list[OutdoorForecastMapped]


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def map_indoor_payload(payload: dict[str, Any]) -> IndoorMapped:
    return IndoorMapped(
        source_id=str(payload.get("id") or "unknown"),
        mac=payload.get("mac"),
        latitude=_as_float(payload.get("latitude")),
        longitude=_as_float(payload.get("longitude")),
        pm1=_as_float(payload.get("pm1")),
        pm25=_as_float(payload.get("pm25")),
        pm10=_as_float(payload.get("pm10")),
        temperature_c=_as_float(payload.get("temperature")),
        humidity_pct=_as_float(payload.get("humidity")),
        recorded_at_utc=utc_now(),
        raw_json=payload,
    )


def _iaqi_value(data: dict[str, Any], key: str) -> float | None:
    node = data.get("iaqi", {}).get(key, {})
    return _as_float(node.get("v")) if isinstance(node, dict) else None


def _extract_forecasts(data: dict[str, Any]) -> list[OutdoorForecastMapped]:
    forecasts: list[OutdoorForecastMapped] = []
    daily = data.get("forecast", {}).get("daily", {})
    if not isinstance(daily, dict):
        return forecasts

    for forecast_type, items in daily.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict) or "day" not in item:
                continue
            forecasts.append(
                OutdoorForecastMapped(
                    forecast_type=str(forecast_type),
                    forecast_day=date.fromisoformat(item["day"]),
                    avg_value=_as_float(item.get("avg")),
                    min_value=_as_float(item.get("min")),
                    max_value=_as_float(item.get("max")),
                    raw_json=item,
                )
            )
    return forecasts


def map_outdoor_payload(payload: dict[str, Any]) -> OutdoorMapped:
    data = payload.get("data", {}) if isinstance(payload, dict) else {}
    city = data.get("city", {}) if isinstance(data, dict) else {}
    geo = city.get("geo", []) if isinstance(city, dict) else []
    source_time = None
    time_data = data.get("time", {}) if isinstance(data, dict) else {}
    if isinstance(time_data, dict) and time_data.get("iso"):
        source_time = parse_datetime_to_utc(time_data["iso"])

    latitude = _as_float(geo[0]) if len(geo) > 0 else None
    longitude = _as_float(geo[1]) if len(geo) > 1 else None

    return OutdoorMapped(
        recorded_at_utc=utc_now(),
        source_time_utc=source_time,
        waqi_idx=data.get("idx"),
        city_name=city.get("name"),
        latitude=latitude,
        longitude=longitude,
        aqi=_as_float(data.get("aqi")),
        dominant_pollutant=data.get("dominentpol"),
        co=_iaqi_value(data, "co"),
        h=_iaqi_value(data, "h"),
        no2=_iaqi_value(data, "no2"),
        o3=_iaqi_value(data, "o3"),
        p=_iaqi_value(data, "p"),
        pm25=_iaqi_value(data, "pm25"),
        so2=_iaqi_value(data, "so2"),
        t=_iaqi_value(data, "t"),
        w=_iaqi_value(data, "w"),
        raw_json=payload,
        forecasts=_extract_forecasts(data),
    )
