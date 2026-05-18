from __future__ import annotations

import importlib

import dash

from adsreport.i18n import set_locale


def _find_by_id(node: object, component_id: str) -> object | None:
    if getattr(node, "id", None) == component_id:
        return node
    children = getattr(node, "children", None)
    if children is None:
        return None
    if isinstance(children, list):
        for child in children:
            found = _find_by_id(child, component_id)
            if found is not None:
                return found
        return None
    return _find_by_id(children, component_id)


def test_dashboard_has_a4_pdf_export_button(monkeypatch) -> None:
    monkeypatch.setattr(dash, "register_page", lambda *args, **kwargs: None)
    dashboard_page = importlib.import_module("adsreport.ui.pages.dashboard")
    set_locale("en-US")

    rendered = dashboard_page.layout()
    button = _find_by_id(rendered, "dashboard-export-pdf-btn")
    download = _find_by_id(rendered, "dashboard-pdf-download")
    status = _find_by_id(rendered, "dashboard-export-status")
    report = _find_by_id(rendered, "dashboard-report")

    assert button is not None
    assert button.children == "Export A4 PDF"
    assert download is not None
    assert status is not None
    assert report is not None
    assert report.className == "dashboard-report-a4"
