from __future__ import annotations

from datetime import datetime


def coerce_float(value: float | int | str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def format_compact_currency(value: float | int | str | None) -> str:
    amount = coerce_float(value)
    if amount is None:
        return "-"

    sign = "-" if amount < 0 else ""
    amount = abs(amount)

    if amount >= 1_000_000_000:
        return f"{sign}{amount / 1_000_000_000:.2f}B"
    if amount >= 1_000_000:
        return f"{sign}{amount / 1_000_000:.2f}M"
    if amount >= 1_000:
        return f"{sign}{amount / 1_000:.2f}K"
    if amount >= 1:
        return f"{sign}{amount:.2f}"
    if amount == 0:
        return "0"
    return f"{sign}{amount:.4f}"


def format_full_currency(value: float | int | str | None) -> str:
    amount = coerce_float(value)
    if amount is None:
        return "-"
    if amount == 0:
        return "$0.00"
    if abs(amount) >= 1:
        return f"${amount:,.2f}"
    return f"${amount:,.8f}"


def parse_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value

    if isinstance(value, (int, float)):
        timestamp = float(value)
        if timestamp > 1_000_000_000_000:
            timestamp /= 1000
        try:
            return datetime.fromtimestamp(timestamp)
        except (OSError, OverflowError, ValueError):
            return None

    text = str(value or "").strip()
    if not text:
        return None

    iso_text = text.replace("Z", "+00:00")
    for candidate in (iso_text, iso_text.replace("T", " ")):
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            continue

    normalized = text.replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            continue

    return None


def format_created_at(value: object) -> str:
    parsed = parse_datetime(value)
    if parsed is not None:
        return parsed.strftime("%Y-%m-%d %H:%M")

    text = str(value or "").replace("T", " ").strip()
    if not text:
        return "-"
    return text[:16]


def format_age(value: object) -> str:
    created_at = parse_datetime(value)
    if created_at is None:
        return "-"

    now = datetime.now(created_at.tzinfo) if created_at.tzinfo is not None else datetime.now()
    elapsed_seconds = max((now - created_at).total_seconds(), 0)
    total_minutes = int(elapsed_seconds // 60)
    days, remaining_minutes = divmod(total_minutes, 24 * 60)
    hours, minutes = divmod(remaining_minutes, 60)

    if days:
        return f"{days}d {hours:02d}h"
    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m"
    return "<1m"


def matches_query(query: str, *values: object) -> bool:
    normalized = query.strip().casefold()
    if not normalized:
        return True

    haystack = " ".join("" if value is None else str(value) for value in values).casefold()
    return normalized in haystack
