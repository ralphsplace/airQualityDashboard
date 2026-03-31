
from datetime import date

from app.schemas.forecast import ForecastItem
from app.services.forecast_transform import pivot_to_by_date

def test_pivot_to_by_date():
    raw = {
        "pm25": [
            ForecastItem(day=date(2026, 3, 31), avg=12, min=8, max=20),
            ForecastItem(day=date(2026, 4, 1), avg=15, min=10, max=25),
        ],
        "pm10": [
            ForecastItem(day=date(2026, 3, 31), avg=20, min=15, max=30),
            ForecastItem(day=date(2026, 4, 1), avg=18, min=12, max=28),
        ],
    }

    pdata = pivot_to_by_date(raw)

    assert list(pdata.keys()) == [date(2026, 3, 31), date(2026, 4, 1)]
    assert pdata[date(2026, 3, 31)][0].pollutant == "pm25"
    assert pdata[date(2026, 3, 31)][0].avg == 12
    assert pdata[date(2026, 4, 1)][1].pollutant == "pm10"
    assert pdata[date(2026, 4, 1)][1].avg == 18