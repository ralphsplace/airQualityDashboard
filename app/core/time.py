from __future__ import annotations

from datetime import datetime, timedelta, timezone

UTC = timezone.utc


def utc_now() -> datetime:
    return datetime.now(UTC)


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def parse_datetime_to_utc(value: str) -> datetime:
    # Supports strings like 2026-03-30T22:00:00-05:00 and trailing Z.
    normalized = value.replace("Z", "+00:00")
    return ensure_utc(datetime.fromisoformat(normalized))


def to_utc_iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    value = ensure_utc(dt).isoformat()
    return value.replace("+00:00", "Z")


def resolve_range(
    *,
    days: int,
    max_days: int,
    from_utc: datetime | None = None,
    to_utc: datetime | None = None,
) -> tuple[datetime, datetime]:
    if days < 1:
        raise ValueError("days must be >= 1")
    if days > max_days:
        raise ValueError(f"days must be <= {max_days}")

    end = ensure_utc(to_utc) if to_utc else utc_now()
    start = ensure_utc(from_utc) if from_utc else end - timedelta(days=days)

    if start >= end:
        raise ValueError("from_utc must be before to_utc")

    if end - start > timedelta(days=max_days):
        raise ValueError(f"requested range exceeds {max_days} days")

    return start, end
