import pytest

from app.polling.service import PollerService


class FakeIndoorClient:
    async def fetch(self):
        return {
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


class FakeOutdoorClient:
    async def fetch(self):
        return {
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


class BrokenIndoorClient:
    async def fetch(self):
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_poll_once_success(db_session):
    from app.services.repository import AirRepository
    from app.db.models import IndoorReading, OutdoorReading

    service = PollerService(FakeIndoorClient(), FakeOutdoorClient(), interval_seconds=300)
    await service.poll_once()

    assert db_session.query(IndoorReading).count() == 1
    assert db_session.query(OutdoorReading).count() == 1


@pytest.mark.asyncio
async def test_one_failed_source_does_not_stop_other(db_session):
    from app.db.models import IndoorReading, OutdoorReading

    service = PollerService(BrokenIndoorClient(), FakeOutdoorClient(), interval_seconds=300)
    await service.poll_once()

    assert db_session.query(IndoorReading).count() == 0
    assert db_session.query(OutdoorReading).count() == 1
