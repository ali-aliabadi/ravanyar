"""SPEC-0002: allowlisted staging numbers sign in with a fixed code and send no SMS."""

import logging
from collections.abc import Iterator

import pytest
from django.test import Client
from django.test.utils import override_settings

from core.models import Account
from core.tests.conftest import CURRENT, make_phone

pytestmark = [pytest.mark.integration, pytest.mark.django_db]
JSON = "application/json"
TEST_PHONE = make_phone(900)


@pytest.fixture
def test_mode() -> Iterator[None]:
    with override_settings(TEST_PHONES=frozenset({TEST_PHONE}), TEST_CODE="424242"):
        yield


def verify(client: Client, phone: str, code: str) -> int:
    body = {"phone": phone, "code": code, "role": "therapist", **CURRENT}
    return client.post("/api/auth/verify", body, JSON).status_code


@pytest.mark.usefixtures("test_mode")
def test_test_phone_uses_fixed_code_without_sms(
    sent_codes: dict[str, str], caplog: pytest.LogCaptureFixture
) -> None:
    client = Client()
    caplog.set_level(logging.WARNING, logger="core.services")
    assert client.post("/api/auth/code", {"phone": TEST_PHONE}, JSON).status_code == 202
    assert sent_codes == {}
    assert verify(client, TEST_PHONE, "000000") == 400  # still counts as a wrong guess
    assert verify(client, TEST_PHONE, "424242") == 200
    account = Account.objects.get()
    assert f"staging test sign-in account={account.pk}" in caplog.text
    assert TEST_PHONE not in caplog.text


@pytest.mark.usefixtures("test_mode")
def test_other_numbers_still_get_a_real_sms(sent_codes: dict[str, str]) -> None:
    client, phone = Client(), make_phone(901)
    assert client.post("/api/auth/code", {"phone": phone}, JSON).status_code == 202
    assert phone in sent_codes
    if sent_codes[phone] != "424242":
        assert verify(client, phone, "424242") == 400


def test_fixed_code_does_nothing_when_test_mode_is_off(sent_codes: dict[str, str]) -> None:
    client = Client()
    client.post("/api/auth/code", {"phone": TEST_PHONE}, JSON)
    assert TEST_PHONE in sent_codes  # an ordinary number again
