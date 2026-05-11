"""E2E smoke tests using Playwright.

Requires a running AdsReport instance. Set ADSREPORT_TEST_URL env var (default: http://localhost:8050).
"""

from __future__ import annotations

import os

import pytest

BASE_URL = os.environ.get("ADSREPORT_TEST_URL", "http://localhost:8050")

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="session")
def browser_context_args():
    return {"base_url": BASE_URL}


@pytest.mark.skip(reason="Requires running AdsReport instance and Playwright browsers")
def test_login_page_loads(page):
    page.goto("/login")
    assert page.title() == "Login — AdsReport"
    assert page.locator("input#login-username").is_visible()


@pytest.mark.skip(reason="Requires running AdsReport instance and Playwright browsers")
def test_onboarding_redirects_unauthenticated(page):
    page.goto("/")
    page.wait_for_url("**/onboarding")
    assert "onboarding" in page.url


@pytest.mark.skip(reason="Requires running AdsReport instance and Playwright browsers")
def test_full_login_and_dashboard(page):
    page.goto("/login")
    page.fill("input#login-username", "admin")
    page.fill("input#login-password", "testpassword123")
    page.click("button#login-submit")
    page.wait_for_url("**/")
    assert page.locator(".kpi-grid").is_visible()
