from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer

from app.core.time import to_utc_iso


class ApiBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("recorded_at_utc", "source_time_utc", "from_utc", "to_utc", check_fields=False)
    def serialize_dt(self, value: datetime | None):
        return to_utc_iso(value)
