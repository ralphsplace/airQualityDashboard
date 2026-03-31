from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import IndoorReading, OutdoorForecast, OutdoorReading
from app.schemas.forecast import ForecastItem, OutdoorForecastCurrentResponse
from app.schemas.indoor import IndoorCurrentResponse, IndoorHistoryItem, IndoorHistoryResponse
from app.schemas.outdoor import OutdoorCurrentResponse, OutdoorHistoryItem, OutdoorHistoryResponse
from app.services.mappers import IndoorMapped, OutdoorMapped


class AirRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add_indoor_reading(self, mapped: IndoorMapped) -> IndoorReading:
        row = IndoorReading(
            recorded_at_utc=mapped.recorded_at_utc,
            source_id=mapped.source_id,
            mac=mapped.mac,
            latitude=mapped.latitude,
            longitude=mapped.longitude,
            pm1=mapped.pm1,
            pm25=mapped.pm25,
            pm10=mapped.pm10,
            temperature_c=mapped.temperature_c,
            humidity_pct=mapped.humidity_pct,
            raw_json=mapped.raw_json,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def add_outdoor_reading(self, mapped: OutdoorMapped) -> OutdoorReading:
        row = OutdoorReading(
            recorded_at_utc=mapped.recorded_at_utc,
            source_time_utc=mapped.source_time_utc,
            waqi_idx=mapped.waqi_idx,
            city_name=mapped.city_name,
            latitude=mapped.latitude,
            longitude=mapped.longitude,
            aqi=mapped.aqi,
            dominant_pollutant=mapped.dominant_pollutant,
            co=mapped.co,
            h=mapped.h,
            no2=mapped.no2,
            o3=mapped.o3,
            p=mapped.p,
            pm25=mapped.pm25,
            so2=mapped.so2,
            t=mapped.t,
            w=mapped.w,
            raw_json=mapped.raw_json,
            forecasts=[
                OutdoorForecast(
                    forecast_type=item.forecast_type,
                    forecast_day=item.forecast_day,
                    avg_value=item.avg_value,
                    min_value=item.min_value,
                    max_value=item.max_value,
                    raw_json=item.raw_json,
                )
                for item in mapped.forecasts
            ],
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def get_latest_indoor(self) -> IndoorCurrentResponse | None:
        row = self.db.scalar(select(IndoorReading).order_by(desc(IndoorReading.recorded_at_utc)).limit(1))
        if row is None:
            return None
        return IndoorCurrentResponse.model_validate(row)

    def get_indoor_history(self, start: datetime, end: datetime) -> IndoorHistoryResponse:
        rows = self.db.scalars(
            select(IndoorReading)
            .where(IndoorReading.recorded_at_utc >= start, IndoorReading.recorded_at_utc < end)
            .order_by(IndoorReading.recorded_at_utc.asc())
        ).all()
        source_id = rows[0].source_id if rows else None
        items = [
            IndoorHistoryItem(
                recorded_at_utc=row.recorded_at_utc,
                pm1=row.pm1,
                pm25=row.pm25,
                pm10=row.pm10,
                temperature_c=row.temperature_c,
                humidity_pct=row.humidity_pct,
            )
            for row in rows
        ]
        return IndoorHistoryResponse(source_id=source_id, from_utc=start, to_utc=end, items=items)

    def get_latest_outdoor(self) -> OutdoorCurrentResponse | None:
        row = self.db.scalar(select(OutdoorReading).order_by(desc(OutdoorReading.recorded_at_utc)).limit(1))
        if row is None:
            return None
        return OutdoorCurrentResponse.model_validate(row)

    def get_outdoor_history(self, start: datetime, end: datetime) -> OutdoorHistoryResponse:
        rows = self.db.scalars(
            select(OutdoorReading)
            .where(OutdoorReading.recorded_at_utc >= start, OutdoorReading.recorded_at_utc < end)
            .order_by(OutdoorReading.recorded_at_utc.asc())
        ).all()
        items = [OutdoorHistoryItem.model_validate(row) for row in rows]
        return OutdoorHistoryResponse(from_utc=start, to_utc=end, items=items)

    def get_latest_outdoor_forecast(self) -> OutdoorForecastCurrentResponse | None:
        row = self.db.scalar(
            select(OutdoorReading)
            .options(selectinload(OutdoorReading.forecasts))
            .order_by(desc(OutdoorReading.recorded_at_utc))
            .limit(1)
        )
        if row is None:
            return None

        grouped: dict[str, list[ForecastItem]] = defaultdict(list)
        for item in row.forecasts:
            grouped[item.forecast_type].append(
                ForecastItem(day=item.forecast_day, avg=item.avg_value, min=item.min_value, max=item.max_value)
            )
        return OutdoorForecastCurrentResponse(
            source_time_utc=row.source_time_utc,
            city_name=row.city_name,
            forecast=dict(grouped),
        )
