from datetime import datetime, timezone

from app.core.time import parse_datetime_to_utc, resolve_range, to_utc_iso


def test_parse_datetime_to_utc():
    parsed = parse_datetime_to_utc("2026-03-30T22:00:00-05:00")
    assert parsed.hour == 3
    assert parsed.tzinfo == timezone.utc


def test_to_utc_iso_returns_z_suffix():
    value = datetime(2026, 3, 31, 3, 0, 0, tzinfo=timezone.utc)
    assert to_utc_iso(value) == "2026-03-31T03:00:00Z"


def test_resolve_range_rejects_large_requests():
    try:
        resolve_range(days=31, max_days=30)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "<= 30" in str(exc)
