from __future__ import annotations

from datetime import date

from adsreport.core.time import comparison_date_range, date_range


def test_comparison_date_range_for_last_month_uses_previous_calendar_month() -> None:
    prev_from, prev_to = comparison_date_range(
        "last_month",
        date(2026, 4, 1),
        date(2026, 4, 30),
    )

    assert prev_from == date(2026, 3, 1)
    assert prev_to == date(2026, 3, 31)


def test_comparison_date_range_for_january_last_month_uses_previous_year() -> None:
    prev_from, prev_to = comparison_date_range(
        "last_month",
        date(2026, 1, 1),
        date(2026, 1, 31),
    )

    assert prev_from == date(2025, 12, 1)
    assert prev_to == date(2025, 12, 31)


def test_comparison_date_range_for_rolling_period_uses_same_day_count() -> None:
    prev_from, prev_to = comparison_date_range(
        "last_7_days",
        date(2026, 5, 6),
        date(2026, 5, 12),
    )

    assert prev_from == date(2026, 4, 29)
    assert prev_to == date(2026, 5, 5)


def test_date_range_accepts_arbitrary_last_n_days(monkeypatch) -> None:
    class FakeDateTime:
        @classmethod
        def now(cls, tz: object = None) -> object:
            class FakeNow:
                def date(self) -> date:
                    return date(2026, 5, 12)

            return FakeNow()

    monkeypatch.setattr("adsreport.core.time.datetime", FakeDateTime)

    date_from, date_to = date_range("last_90_days", "UTC")

    assert date_from == date(2026, 2, 12)
    assert date_to == date(2026, 5, 12)
