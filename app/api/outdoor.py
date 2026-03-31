from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.time import resolve_range
from app.schemas.forecast import OutdoorForecastByDateResponse, OutdoorForecastCurrentResponse
from app.schemas.outdoor import OutdoorCurrentResponse, OutdoorHistoryResponse
from app.services.repository import AirRepository
from app.services.forecast_transform import pivot_to_by_date

router = APIRouter(prefix="/api/v1/outdoor", tags=["outdoor"])


@router.get("/current", response_model=OutdoorCurrentResponse)
def get_current_outdoor(db: Session = Depends(get_db)) -> OutdoorCurrentResponse:
    result = AirRepository(db).get_latest_outdoor()
    if result is None:
        raise HTTPException(status_code=404, detail="No outdoor readings available")
    return result


@router.get("/history", response_model=OutdoorHistoryResponse)
def get_outdoor_history(
    days: int = Query(default=settings.history_default_days, ge=1),
    from_utc: datetime | None = Query(default=None),
    to_utc: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
) -> OutdoorHistoryResponse:
    try:
        start, end = resolve_range(days=days, max_days=settings.history_max_days, from_utc=from_utc, to_utc=to_utc)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AirRepository(db).get_outdoor_history(start, end)


@router.get("/forecast/current", response_model=OutdoorForecastCurrentResponse)
def get_current_forecast(db: Session = Depends(get_db)) -> OutdoorForecastCurrentResponse:
    result = AirRepository(db).get_latest_outdoor_forecast()
    if result is None:
        raise HTTPException(status_code=404, detail="No outdoor forecast available")
    return result


@router.get("/forecast/by-date", response_model=OutdoorForecastByDateResponse)
def get_forecast_by_date_api(
    db: Session = Depends(get_db)
) -> OutdoorForecastByDateResponse:
    result = AirRepository(db).get_latest_outdoor_forecast()

    if result is None:
        raise HTTPException(status_code=404, detail="No outdoor forecast available")

    return OutdoorForecastByDateResponse(
        source_time_utc=result.source_time_utc,
        city_name=result.city_name,
        forecast=pivot_to_by_date(result.forecast),
    )