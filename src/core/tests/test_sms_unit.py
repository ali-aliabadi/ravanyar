import logging
import urllib.parse
import urllib.request
from typing import Any

import pytest

from core import sms
from core.errors import SmsUnavailableError
from core.tests.conftest import make_phone

pytestmark = pytest.mark.unit


class FakeResponse:
    def __init__(self, status: int) -> None:
        self.status = status

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def test_sends_lookup_and_logs_status_only(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    seen: list[urllib.request.Request] = []

    def fake_urlopen(request: urllib.request.Request, **kwargs: Any) -> FakeResponse:
        seen.append(request)
        return FakeResponse(200)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    phone = make_phone(42)
    with caplog.at_level(logging.DEBUG):
        sms.send_code(phone, "123456")

    request = seen[0]
    assert request.full_url.startswith("https://api.kavenegar.com/v1/")
    assert request.full_url.endswith("/verify/lookup.json")
    assert phone[3:] not in request.full_url
    assert isinstance(request.data, bytes)
    body = urllib.parse.parse_qs(request.data.decode())
    assert body["receptor"] == ["0" + phone[3:]]
    assert body["token"] == ["123456"]
    assert phone[3:] not in caplog.text
    assert "123456" not in caplog.text


def test_failure_raises_without_echo(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def down(request: urllib.request.Request, **kwargs: Any) -> FakeResponse:
        raise OSError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", down)
    with pytest.raises(SmsUnavailableError):
        sms.send_code(make_phone(42), "123456")
    assert "123456" not in caplog.text
