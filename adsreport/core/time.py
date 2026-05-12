"""Timezone and date range utilities."""

from __future__ import annotations

from calendar import monthrange
from datetime import UTC, date, datetime, timedelta


def utcnow() -> datetime:
    return datetime.now(tz=UTC)


def today_utc() -> date:
    return utcnow().date()


def date_range(preset: str, tz_name: str = "UTC") -> tuple[date, date]:
    """Convert a named preset to (date_from, date_to) in the given timezone."""
    import zoneinfo

    tz = zoneinfo.ZoneInfo(tz_name)
    today = datetime.now(tz=tz).date()
    if preset.startswith("last_") and preset.endswith("_days"):
        days_text = preset.removeprefix("last_").removesuffix("_days")
        if days_text.isdigit():
            days = max(1, int(days_text))
            return today - timedelta(days=days - 1), today

    match preset:
        case "today":
            return today, today
        case "yesterday":
            return today - timedelta(days=1), today - timedelta(days=1)
        case "last_month":
            return _previous_month(today)
        case "mtd":
            return today.replace(day=1), today
        case _:
            raise ValueError(f"Unknown date preset: {preset!r}")


def comparison_date_range(
    preset: str,
    date_from: date,
    date_to: date,
) -> tuple[date, date]:
    """Return the period used to compare against the selected date range."""
    if preset == "last_month":
        return _previous_month(date_from)

    delta = (date_to - date_from).days + 1
    return date_from - timedelta(days=delta), date_from - timedelta(days=1)


def _previous_month(reference: date) -> tuple[date, date]:
    first_this_month = reference.replace(day=1)
    last_previous_month = first_this_month - timedelta(days=1)
    first_previous_month = last_previous_month.replace(day=1)
    return first_previous_month, last_previous_month


def month_range(year: int, month: int) -> tuple[date, date]:
    last_day = monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def format_currency(cents: int, currency: str = "BRL") -> str:
    """Format an integer cent value as a human-readable currency string."""
    amount = cents / 100
    if currency == "BRL":
        return f"R$ {amount:,.2f}"
    if currency == "MIXED":
        return f"MIXED {amount:,.2f}"
    return f"{currency} {amount:,.2f}"


def format_percent(value: float, decimals: int = 2) -> str:
    return f"{value:.{decimals}f}%"


def format_number(value: int | float) -> str:
    if isinstance(value, float):
        return f"{value:,.2f}"
    return f"{value:,}"
