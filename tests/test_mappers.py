from app.services.mappers import map_indoor_payload, map_outdoor_payload


def test_map_indoor_payload():
    payload = {
        "id": "GAIA-A08-e087",
        "mac": "e08796e6fc84",
        "latitude": 43.65,
        "longitude": 79.3878,
        "pm1": 0.5,
        "pm25": 0.681818,
        "pm10": 0.681818,
        "temperature": 30.06663,
        "humidity": 24.19205,
    }
    mapped = map_indoor_payload(payload)
    assert mapped.source_id == "GAIA-A08-e087"
    assert mapped.temperature_c == 30.06663
    assert mapped.humidity_pct == 24.19205


def test_map_outdoor_payload_with_missing_fields_defaults_to_none():
    payload = {
        "status": "ok",
        "data": {
            "aqi": 65,
            "idx": 5914,
            "city": {"geo": [43.653226, -79.3831843], "name": "Toronto"},
            "dominentpol": "pm25",
            "iaqi": {"pm25": {"v": 65}},
            "time": {"iso": "2026-03-30T22:00:00-05:00"},
            "forecast": {"daily": {"pm25": [{"avg": 41, "day": "2026-03-31", "max": 65, "min": 25}]}},
        },
    }
    mapped = map_outdoor_payload(payload)
    assert mapped.city_name == "Toronto"
    assert mapped.pm25 == 65.0
    assert mapped.co is None
    assert mapped.source_time_utc.isoformat().endswith("+00:00")
    assert len(mapped.forecasts) == 1
    assert mapped.forecasts[0].forecast_type == "pm25"
