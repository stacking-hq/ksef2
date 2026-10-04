"""Parsing of the HTTP ``Retry-After`` header."""

import math
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime


def _now() -> datetime:
    return datetime.now(UTC)


def parse_retry_after(value: str | None) -> float | None:
    """Read a ``Retry-After`` header value in its seconds or HTTP-date form.

    Args:
        value: Header value, or ``None`` when the header is absent.

    Returns:
        Seconds to wait, never negative; ``None`` if absent or not understood.
    """
    if value is None:
        return None
    value = value.strip()
    try:
        seconds = float(value)
    except ValueError:
        try:
            when = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None
        if when.tzinfo is None:
            when = when.replace(tzinfo=UTC)
        seconds = (when - _now()).total_seconds()
    if not math.isfinite(seconds):
        return None
    return max(0.0, seconds)
