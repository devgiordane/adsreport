from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from unittest.mock import MagicMock

from dash import html

from adsreport.i18n import set_locale
from adsreport.ui.callbacks import dashboard_callbacks


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _count_by_id(node: object, component_id: str) -> int:
    if getattr(node, "id", None) == component_id:
        return 1
    children = getattr(node, "children", None)
    if children is None:
        return 0
    if isinstance(children, list):
        return sum(_count_by_id(child, component_id) for child in children)
    return _count_by_id(children, component_id)


# ---------------------------------------------------------------------------
# _normalize_ids
# ---------------------------------------------------------------------------


def test_normalize_ids_none_returns_empty():
    assert dashboard_callbacks._normalize_ids(None) == []


def test_normalize_ids_string_returns_single_item():
    assert dashboard_callbacks._normalize_ids("acc-1") == ["acc-1"]


def test_normalize_ids_list_filters_empty_strings():
    assert dashboard_callbacks._normalize_ids(["a", "", "b", ""]) == ["a", "b"]


def test_normalize_ids_empty_list_returns_empty():
    assert dashboard_callbacks._normalize_ids([]) == []


def test_normalize_ids_valid_list_unchanged():
    assert dashboard_callbacks._normalize_ids(["x", "y"]) == ["x", "y"]


# ---------------------------------------------------------------------------
# _select_accounts
# ---------------------------------------------------------------------------


def _make_account(account_id: str) -> object:
    a = MagicMock()
    a.id = account_id
    return a


def test_select_accounts_returns_matching_accounts():
    a1 = _make_account("id-1")
    a2 = _make_account("id-2")
    repo = MagicMock()
    repo.get_by_id.side_effect = lambda aid: {"id-1": a1, "id-2": a2}.get(aid)

    result = dashboard_callbacks._select_accounts(["id-1", "id-2"], repo)

    assert result == [a1, a2]


def test_select_accounts_skips_unknown_ids():
    repo = MagicMock()
    repo.get_by_id.return_value = None

    result = dashboard_callbacks._select_accounts(["unknown"], repo)

    assert result == []


def test_select_accounts_no_ids_uses_default():
    default = _make_account("default")
    repo = MagicMock()
    repo.get_default.return_value = default

    result = dashboard_callbacks._select_accounts([], repo)

    assert result == [default]
    repo.get_all_active.assert_not_called()


def test_select_accounts_no_ids_no_default_uses_active():
    active = [_make_account("a"), _make_account("b")]
    repo = MagicMock()
    repo.get_default.return_value = None
    repo.get_all_active.return_value = active

    result = dashboard_callbacks._select_accounts([], repo)

    assert result == active


# ---------------------------------------------------------------------------
# _resolve_currency
# ---------------------------------------------------------------------------


def test_resolve_currency_single():
    assert dashboard_callbacks._resolve_currency(["USD", "USD"]) == "USD"


def test_resolve_currency_mixed():
    assert dashboard_callbacks._resolve_currency(["BRL", "USD"]) == "MIXED"


def test_resolve_currency_empty_list_defaults_to_brl():
    assert dashboard_callbacks._resolve_currency([]) == "BRL"


def test_resolve_currency_all_empty_strings_defaults_to_brl():
    assert dashboard_callbacks._resolve_currency(["", ""]) == "BRL"


# ---------------------------------------------------------------------------
# _kpi_cards
# ---------------------------------------------------------------------------


class _Summary:
    impressions = 1000
    clicks = 50
    ctr = 5.0
    cpc_cents = 200
    cpm_cents = 1000
    spend_cents = 10000
    leads = 20
    conversions = 8
    cost_per_lead_cents = 500
    roas = 0.0
    has_roas = False


def test_lead_dashboard_cards_hide_conversions_and_zero_roas() -> None:
    set_locale("en-US")

    cards = dashboard_callbacks._kpi_cards(_Summary(), _Summary(), "BRL")
    labels = [card.children[0].children for card in cards]
    values = [card.children[1].children for card in cards]

    assert "Leads" in labels
    assert "Cost per lead" in labels
    assert "Conversions" not in labels
    assert "ROAS" not in labels
    assert "20" in values
    assert "R$ 5.00" in values


def test_kpi_cards_include_roas_when_flagged() -> None:
    set_locale("en-US")

    class SummaryWithRoas(_Summary):
        roas = 3.5
        has_roas = True

    s = SummaryWithRoas()
    cards = dashboard_callbacks._kpi_cards(s, s, "BRL")
    labels = [card.children[0].children for card in cards]

    assert "ROAS" in labels
    assert len(cards) == 9


def test_money_fields_use_selected_account_currency() -> None:
    set_locale("en-US")

    class Summary(_Summary):
        cpc_cents = 72
        cpm_cents = 3868
        spend_cents = 17404
        cost_per_lead_cents = 645

    cards = dashboard_callbacks._kpi_cards(Summary(), Summary(), "USD")
    values = [card.children[1].children for card in cards]

    assert "USD 0.72" in values
    assert "USD 38.68" in values
    assert "USD 174.04" in values
    assert "USD 6.45" in values
    assert "R$ 174.04" not in values


def test_kpi_delta_is_none_when_prev_is_zero() -> None:
    set_locale("en-US")

    class ZeroPrev(_Summary):
        impressions = 0
        clicks = 0
        ctr = 0.0
        cpc_cents = 0
        cpm_cents = 0
        spend_cents = 0
        leads = 0
        cost_per_lead_cents = 0

    cards = dashboard_callbacks._kpi_cards(_Summary(), ZeroPrev(), "BRL")

    for card in cards:
        delta_el = card.children[2]
        assert delta_el.children is None


# ---------------------------------------------------------------------------
# _leads_timeseries_block
# ---------------------------------------------------------------------------


def test_timeseries_chart_shows_daily_leads_with_legend() -> None:
    set_locale("en-US")

    @dataclass
    class Point:
        date: date
        leads: int

    block = dashboard_callbacks._leads_timeseries_block(
        [Point(date(2026, 5, 1), 3), Point(date(2026, 5, 2), 8)],
        {"layout": {}},
    )

    graph = block.children[1]
    fig = graph.figure

    assert block.children[0].children == "Leads by day"
    assert fig.data[0].name == "Generated leads"
    assert list(fig.data[0].y) == [3, 8]
    assert fig.layout.showlegend is True
    assert fig.layout.yaxis.title.text == "Leads"


# ---------------------------------------------------------------------------
# _build_breakdown_block
# ---------------------------------------------------------------------------


def test_build_breakdown_block_limits_to_8_campaigns() -> None:
    set_locale("en-US")

    @dataclass
    class Camp:
        name: str
        spend_cents: int

    campaigns = [Camp(f"C{i}", i * 1000) for i in range(12)]
    block = dashboard_callbacks._build_breakdown_block(campaigns, {"layout": {}})
    graph = block.children[1]
    fig = graph.figure

    assert len(fig.data[0].x) == 8
    assert fig.data[0].x[0] == "C0"


def test_build_breakdown_block_empty_campaigns() -> None:
    set_locale("en-US")

    block = dashboard_callbacks._build_breakdown_block([], {"layout": {}})
    graph = block.children[1]
    fig = graph.figure

    assert len(fig.data[0].x) == 0


# ---------------------------------------------------------------------------
# _entity_rows
# ---------------------------------------------------------------------------


def test_entity_rows_use_names_not_ids() -> None:
    class Row:
        name = "Campaign Name"
        entity_id = "camp_123"
        spend_cents = 10000
        impressions = 1000
        clicks = 50
        ctr = 5.0
        roas = 0.0
        leads = 20
        cost_per_lead_cents = 500

    rows = dashboard_callbacks._entity_rows([Row()])

    assert rows[0]["entity_id"] == "Campaign Name"
    assert rows[0]["leads"] == "20"
    assert rows[0]["cost_per_lead"] == "R$ 5.00"


# ---------------------------------------------------------------------------
# _build_campaign_tables
# ---------------------------------------------------------------------------


@dataclass
class _CampaignRow:
    name: str
    spend_cents: int = 10000
    impressions: int = 1000
    clicks: int = 50
    ctr: float = 5.0
    roas: float = 0.0
    leads: int = 20
    cost_per_lead_cents: int = 500


@dataclass
class _ReportData:
    summary: object
    top_campaigns: list = field(default_factory=list)
    top_adsets: list = field(default_factory=list)


def _get_datatable(wrapper: object) -> object:
    """data_table returns html.Div([H3, DataTable]); get the inner DataTable."""
    return wrapper.children[1]


def test_build_campaign_tables_no_roas_excludes_roas_column() -> None:
    set_locale("en-US")

    class SummaryNoRoas(_Summary):
        has_roas = False

    report = _ReportData(summary=SummaryNoRoas(), top_campaigns=[_CampaignRow("C1")])
    table_div = dashboard_callbacks._build_campaign_tables(report, "BRL")

    col_ids = [c["id"] for c in _get_datatable(table_div.children[0]).columns]

    assert "roas" not in col_ids
    assert len(table_div.children) == 1


def test_build_campaign_tables_with_roas_includes_roas_column() -> None:
    set_locale("en-US")

    class SummaryRoas(_Summary):
        has_roas = True

    report = _ReportData(summary=SummaryRoas(), top_campaigns=[_CampaignRow("C1")])
    table_div = dashboard_callbacks._build_campaign_tables(report, "BRL")

    col_ids = [c["id"] for c in _get_datatable(table_div.children[0]).columns]
    assert "roas" in col_ids


def test_build_campaign_tables_includes_adsets_table_when_present() -> None:
    set_locale("en-US")

    class SummaryNoRoas(_Summary):
        has_roas = False

    report = _ReportData(
        summary=SummaryNoRoas(),
        top_campaigns=[_CampaignRow("C1")],
        top_adsets=[_CampaignRow("AS1")],
    )
    table_div = dashboard_callbacks._build_campaign_tables(report, "BRL")

    assert len(table_div.children) == 2
    assert _get_datatable(table_div.children[1]).id == "dashboard-adsets-table"


def test_build_campaign_tables_adset_column_label_differs_from_campaign() -> None:
    set_locale("en-US")

    class SummaryNoRoas(_Summary):
        has_roas = False

    report = _ReportData(
        summary=SummaryNoRoas(),
        top_campaigns=[_CampaignRow("C1")],
        top_adsets=[_CampaignRow("AS1")],
    )
    table_div = dashboard_callbacks._build_campaign_tables(report, "BRL")

    campaign_first_col = _get_datatable(table_div.children[0]).columns[0]
    adset_first_col = _get_datatable(table_div.children[1]).columns[0]

    assert campaign_first_col["name"] == "Campaign"
    assert adset_first_col["name"] == "Ad set"


# ---------------------------------------------------------------------------
# _empty_dashboard
# ---------------------------------------------------------------------------


def test_empty_dashboard_renders_one_sync_button():
    set_locale("en-US")

    rendered = dashboard_callbacks._empty_dashboard()

    assert sum(_count_by_id(part, "dashboard-sync-btn") for part in rendered) == 1


# ---------------------------------------------------------------------------
# trigger_dashboard_sync
# ---------------------------------------------------------------------------


def test_trigger_dashboard_sync_uses_selected_account_ids(monkeypatch):
    calls = []

    class FakeScheduler:
        def trigger_sync_now(self, triggered_by="manual", account_ids=None):
            calls.append((triggered_by, account_ids))

    monkeypatch.setattr(dashboard_callbacks, "SchedulerService", FakeScheduler)
    set_locale("en-US")

    result = dashboard_callbacks.trigger_dashboard_sync(1, ["account-1", ""])

    assert calls == [("manual", ["account-1"])]
    assert isinstance(result, html.Span)
    assert result.style["color"] == "var(--success)"


def test_trigger_dashboard_sync_returns_no_update_for_zero_clicks(monkeypatch):
    from dash import no_update

    result = dashboard_callbacks.trigger_dashboard_sync(0, None)

    assert result is no_update


def test_trigger_dashboard_sync_returns_error_span_on_exception(monkeypatch):
    class BrokenScheduler:
        def trigger_sync_now(self, **kwargs):
            raise RuntimeError("scheduler down")

    monkeypatch.setattr(dashboard_callbacks, "SchedulerService", BrokenScheduler)
    set_locale("en-US")

    result = dashboard_callbacks.trigger_dashboard_sync(1, None)

    assert isinstance(result, html.Span)
    assert result.style["color"] == "var(--danger)"
    assert "Could not start sync" in result.children
