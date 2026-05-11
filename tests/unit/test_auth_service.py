from __future__ import annotations

import pytest

from adsreport.core.errors import AuthError
from adsreport.services.auth_service import AuthService
from tests.factories import UserFactory


def test_create_admin_success(session):
    svc = AuthService()
    result = svc.create_admin("admin", "correctpassword")
    assert result.is_ok()
    user = result.unwrap()
    assert user.username == "admin"


def test_create_admin_password_too_short(session):
    svc = AuthService()
    result = svc.create_admin("admin", "short")
    assert result.is_err()
    assert "8 characters" in str(result.unwrap_err())


def test_login_success(session):
    svc = AuthService()
    svc.create_admin("admin", "correctpassword")
    result = svc.login("admin", "correctpassword")
    assert result.is_ok()


def test_login_wrong_password(session):
    svc = AuthService()
    svc.create_admin("admin", "correctpassword")
    result = svc.login("admin", "wrongpassword")
    assert result.is_err()


def test_login_unknown_user(session):
    svc = AuthService()
    result = svc.login("ghost", "anything")
    assert result.is_err()


def test_duplicate_username_rejected(session):
    svc = AuthService()
    svc.create_admin("admin", "firstpassword1")
    result = svc.create_admin("admin", "secondpassword1")
    assert result.is_err()
