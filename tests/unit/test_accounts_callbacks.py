from __future__ import annotations

from datetime import UTC, datetime

from dash import dash_table

from adsreport.i18n import set_locale
from adsreport.repositories.ad_account_repo import AdAccountRepository
from adsreport.ui.callbacks import accounts_callbacks
from adsreport.ui.components.accounts_list import accounts_list
from tests.factories import AdAccountFactory


def test_render_accounts_lists_saved_accounts(session):
    set_locale("en-US")
    account = AdAccountFactory.create(
        fb_account_id="act_123",
        name="Main Client",
        is_default=True,
        sync_enabled=True,
        last_synced_at=datetime(2026, 5, 11, 12, 30, tzinfo=UTC),
    )
    session.add(account)
    session.commit()

    rendered = accounts_list()
    table = next(child for child in rendered.children if isinstance(child, dash_table.DataTable))

    assert table.data == [
        {
            "name": "Main Client (Default)",
            "id": account.id,
            "fb_account_id": "act_123",
            "status": "Active",
            "currency": "BRL",
            "timezone": "America/Sao_Paulo",
            "last_synced_at": "2026-05-11 12:30",
            "sync_action": "Sync now",
            "account_id": account.id,
            "sync_enabled": "true",
        }
    ]
    assert table.selected_row_ids == [account.id]
    assert table.columns[-1] == {"name": "Actions", "id": "sync_action"}


def test_render_accounts_shows_empty_state_when_no_accounts():
    set_locale("en-US")

    rendered = accounts_list()

    assert rendered.className == "empty-state"
    assert "No ad accounts" in str(rendered.children)


def test_sync_account_from_table_triggers_selected_account(monkeypatch):
    calls = []

    class FakeSchedulerService:
        def trigger_sync_range_now(
            self,
            triggered_by: str = "manual",
            account_ids: list[str] | None = None,
            date_preset: str | None = None,
        ) -> None:
            calls.append((triggered_by, account_ids, date_preset))

    monkeypatch.setattr(accounts_callbacks, "SchedulerService", FakeSchedulerService)
    set_locale("en-US")

    result = accounts_callbacks.sync_account_from_table(
        {"row": 0, "row_id": "account-1", "column_id": "sync_action"},
        None,
        None,
        [{"account_id": "account-1"}],
        [],
        "last_90_days",
    )

    assert calls == [("manual", ["account-1"], "last_90_days")]
    assert "Sync started" in str(result.children)


def test_sync_selected_accounts_from_table(monkeypatch):
    calls = []

    class FakeSchedulerService:
        def trigger_sync_range_now(
            self,
            triggered_by: str = "manual",
            account_ids: list[str] | None = None,
            date_preset: str | None = None,
        ) -> None:
            calls.append((triggered_by, account_ids, date_preset))

    monkeypatch.setattr(accounts_callbacks, "SchedulerService", FakeSchedulerService)
    monkeypatch.setattr(accounts_callbacks, "_triggered_id", lambda: "accounts-sync-selected-btn")
    set_locale("en-US")

    accounts_callbacks.sync_account_from_table(
        None,
        1,
        None,
        [{"account_id": "account-1"}, {"account_id": "account-2"}],
        ["account-1"],
        "last_365_days",
    )

    assert calls == [("manual", ["account-1"], "last_365_days")]


def test_sync_all_accounts_from_table(monkeypatch):
    calls = []

    class FakeSchedulerService:
        def trigger_sync_range_now(
            self,
            triggered_by: str = "manual",
            account_ids: list[str] | None = None,
            date_preset: str | None = None,
        ) -> None:
            calls.append((triggered_by, account_ids, date_preset))

    monkeypatch.setattr(accounts_callbacks, "SchedulerService", FakeSchedulerService)
    monkeypatch.setattr(accounts_callbacks, "_triggered_id", lambda: "accounts-sync-all-btn")

    accounts_callbacks.sync_account_from_table(
        None,
        None,
        1,
        [{"account_id": "account-1"}, {"account_id": "account-2"}],
        ["account-1"],
        "last_90_days",
    )

    assert calls == [("manual", ["account-1", "account-2"], "last_90_days")]


def test_save_account_sync_selection_persists_checked_rows(session):
    account = AdAccountFactory.create(sync_enabled=False)
    other = AdAccountFactory.create(sync_enabled=True)
    session.add_all([account, other])
    session.commit()

    accounts_callbacks.save_account_sync_selection([account.id])
    session.refresh(account)
    session.refresh(other)

    assert account.sync_enabled is True
    assert other.sync_enabled is False


def test_default_account_is_sync_enabled_without_enabling_others(session):
    default = AdAccountFactory.create(sync_enabled=False)
    other = AdAccountFactory.create(sync_enabled=False)
    session.add_all([default, other])
    session.commit()

    AdAccountRepository(session).set_default(default.id)
    session.refresh(default)
    session.refresh(other)

    assert default.is_default is True
    assert default.sync_enabled is True
    assert other.sync_enabled is False
