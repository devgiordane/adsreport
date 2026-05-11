from __future__ import annotations

import json

import pytest
from facebook_business.exceptions import FacebookRequestError

from adsreport.core.errors import FacebookError, FacebookRateLimitError
from adsreport.services.facebook_client import FacebookClient


def _request_error(code: int, message: str, status: int = 400) -> FacebookRequestError:
    body = json.dumps({"error": {"message": message, "code": code}})
    return FacebookRequestError(
        message,
        {"method": "GET", "path": "/act_123/insights", "params": {}},
        status,
        {},
        body,
    )


def test_handle_exc_classifies_facebook_token_error():
    client = FacebookClient.__new__(FacebookClient)
    exc = _request_error(190, "Invalid OAuth access token.")

    with pytest.raises(FacebookError) as raised:
        client._handle_exc(exc)

    assert raised.value.status_code == 190
    assert "Access token error" in str(raised.value)


def test_handle_exc_classifies_facebook_rate_limit_error():
    client = FacebookClient.__new__(FacebookClient)
    exc = _request_error(17, "User request limit reached.")

    with pytest.raises(FacebookRateLimitError):
        client._handle_exc(exc)
