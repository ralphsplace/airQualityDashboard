from __future__ import annotations

from collections import defaultdict
from datetime import date

from app.schemas.forecast import ForecastItem, ForecastPollutant


def pivot_to_by_date(
    forecast: dict[str, list[ForecastItem]],
) -> dict[date, list[ForecastPollutant]]:
    by_date: dict[date, list[ForecastPollutant]] = defaultdict(list)

    for pollutant, items in forecast.items():
        for entry in items:
            
            if entry.day.isoformat().startswith("2025"):
                 continue

            by_date[entry.day].append(
                ForecastPollutant(
                    pollutant=pollutant,
                    avg=entry.avg,
                    min=entry.min,
                    max=entry.max,
                )
            )

    return dict(sorted(by_date.items()))