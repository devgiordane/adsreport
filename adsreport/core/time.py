"""Timezone and date range utilities."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone


def utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def today_utc() -> date:
    return utcnow().date()


def date_range(preset: str, tz_name: str = "UTC") -> tuple[date, date]:
    """Convert a named preset to (date_from, date_to) in the given timezone."""
    import zoneinfo

    tz = zoneinfo.ZoneInfo(tz_name)
    today = datetime.now(tz=tz).date()

    match preset:
        case "today":
            return today, today
        case "yesterday":
            return today - timedelta(days=1), today - timedelta(days=1)
        case "last_7_days":
            return today - timedelta(days=6), today
        case "last_14_days":
            return today - timedelta(days=13), today
        case "last_30_days":
            return today - timedelta(days=29), today
        case "mtd":
            return today.replace(day=1), today
        case _:
            raise ValueError(f"Unknown date preset: {preset!r}")


def format_currency(cents: int, currency: str = "BRL") -> str:
    """Format an integer cent value as a human-readable currency string."""
    amount = cents / 100
    if currency == "BRL":
        return f"R$ {amount:,.2f}"
    return f"{currency} {amount:,.2f}"


def format_percent(value: float, decimals: int = 2) -> str:
    return f"{value:.{decimals}f}%"


def format_number(value: int | float) -> str:
    if isinstance(value, float):
        return f"{value:,.2f}"
    return f"{value:,}"
