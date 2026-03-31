from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.time import resolve_range
from app.schemas.indoor import IndoorCurrentResponse, IndoorHistoryResponse
from app.services.repository import AirRepository

router = APIRouter(prefix="/api/v1/indoor", tags=["indoor"])


@router.get("/current", response_model=IndoorCurrentResponse)
def get_current_indoor(db: Session = Depends(get_db)) -> IndoorCurrentResponse:
    result = AirRepository(db).get_latest_indoor()
    if result is None:
        raise HTTPException(status_code=404, detail="No indoor readings available")
    return result


@router.get("/history", response_model=IndoorHistoryResponse)
def get_indoor_history(
    days: int = Query(default=settings.history_default_days, ge=1),
    from_utc: datetime | None = Query(default=None),
    to_utc: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
) -> IndoorHistoryResponse:
    try:
        start, end = resolve_range(days=days, max_days=settings.history_max_days, from_utc=from_utc, to_utc=to_utc)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AirRepository(db).get_indoor_history(start, end)
