from datetime import date, datetime, timezone

from app.db.models import IndoorReading, OutdoorForecast, OutdoorReading


def seed_data(db_session):
    indoor = IndoorReading(
        recorded_at_utc=datetime(2026, 3, 31, 3, 24, 26, tzinfo=timezone.utc),
        source_id="GAIA-A08-e087",
        mac="e08796e6fc84",
        latitude=43.65,
        longitude=79.3878,
        pm1=0.5,
        pm25=0.681818,
        pm10=0.681818,
        temperature_c=30.06663,
        humidity_pct=24.19205,
        raw_json={},
    )
    outdoor = OutdoorReading(
        recorded_at_utc=datetime(2026, 3, 31, 3, 24, 26, tzinfo=timezone.utc),
        source_time_utc=datetime(2026, 3, 31, 3, 0, 0, tzinfo=timezone.utc),
        waqi_idx=5914,
        city_name="Toronto",
        latitude=43.653226,
        longitude=-79.3831843,
        aqi=65,
        dominant_pollutant="pm25",
        co=3.0,
        h=65.2,
        no2=27.8,
        o3=16.8,
        p=1013.1,
        pm25=65.0,
        so2=0.9,
        t=17.3,
        w=1.0,
        raw_json={},
        forecasts=[
            OutdoorForecast(
                forecast_type="pm25",
                forecast_day=date(2026, 3, 31),
                avg_value=41,
                min_value=25,
                max_value=65,
                raw_json={},
            )
        ],
    )
    db_session.add(indoor)
    db_session.add(outdoor)
    db_session.commit()


def test_get_indoor_current(client, db_session):
    seed_data(db_session)
    response = client.get("/api/v1/indoor/current")
    assert response.status_code == 200
    body = response.json()
    assert body["source_id"] == "GAIA-A08-e087"
    assert body["pm25"] == 0.681818


def test_get_indoor_history(client, db_session):
    seed_data(db_session)
    response = client.get("/api/v1/indoor/history?days=7")
    assert response.status_code == 200
    body = response.json()
    assert body["source_id"] == "GAIA-A08-e087"
    assert len(body["items"]) == 1


def test_get_outdoor_current(client, db_session):
    seed_data(db_session)
    response = client.get("/api/v1/outdoor/current")
    assert response.status_code == 200
    body = response.json()
    assert body["city_name"] == "Toronto"
    assert body["aqi"] == 65.0


def test_get_outdoor_history(client, db_session):
    seed_data(db_session)
    response = client.get("/api/v1/outdoor/history?days=7")
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["pm25"] == 65.0


def test_get_outdoor_forecast_current(client, db_session):
    seed_data(db_session)
    response = client.get("/api/v1/outdoor/forecast/current")
    assert response.status_code == 200
    body = response.json()
    assert body["city_name"] == "Toronto"
    assert body["forecast"]["pm25"][0]["max"] == 65.0
