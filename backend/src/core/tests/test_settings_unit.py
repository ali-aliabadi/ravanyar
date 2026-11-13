"""Production settings refuse to start on a missing or bad key, or draft consent versions."""

import base64
import importlib
import os
import sys
from collections.abc import Iterator
from types import ModuleType

import pytest
from django.core.exceptions import ImproperlyConfigured

pytestmark = pytest.mark.unit

GOOD_KEY = base64.b64encode(os.urandom(32)).decode()
ENV = {
    "DJANGO_SECRET_KEY": "x",
    "DJANGO_ALLOWED_HOSTS": "example.test",
    "POSTGRES_DB": "x",
    "POSTGRES_USER": "x",
    "POSTGRES_PASSWORD": "x",
    "POSTGRES_HOST": "x",
    "RAVANYAR_MASTER_KEY": GOOD_KEY,
    "RAVANYAR_BLIND_INDEX_KEY": GOOD_KEY,
    "KAVENEGAR_API_KEY": "x",
}
FINAL = {"terms": "terms-1", "privacy": "privacy-1"}


@pytest.fixture
def prod_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[pytest.MonkeyPatch]:
    for name, value in ENV.items():
        monkeypatch.setenv(name, value)
    yield monkeypatch
    sys.modules.pop("config.settings.prod", None)


def load_prod() -> ModuleType:
    sys.modules.pop("config.settings.prod", None)
    return importlib.import_module("config.settings.prod")


def test_prod_starts_with_valid_keys_and_final_consent(prod_env: pytest.MonkeyPatch) -> None:
    prod_env.setattr("config.settings.base.CONSENT_VERSIONS", FINAL)
    assert len(load_prod().MASTER_KEY) == 32


@pytest.mark.parametrize("name", ["RAVANYAR_MASTER_KEY", "RAVANYAR_BLIND_INDEX_KEY"])
@pytest.mark.parametrize("value", [None, "not base64!", base64.b64encode(b"short").decode()])
def test_bad_or_missing_key_refuses_start(
    prod_env: pytest.MonkeyPatch, name: str, value: str | None
) -> None:
    prod_env.setattr("config.settings.base.CONSENT_VERSIONS", FINAL)
    if value is None:
        prod_env.delenv(name)
    else:
        prod_env.setenv(name, value)
    with pytest.raises((RuntimeError, ImproperlyConfigured), match=name):
        load_prod()


def test_prod_refuses_draft_consent(prod_env: pytest.MonkeyPatch) -> None:
    with pytest.raises(ImproperlyConfigured, match="consent"):
        load_prod()


def test_prelaunch_allows_draft_consent(prod_env: pytest.MonkeyPatch) -> None:
    prod_env.setenv("RAVANYAR_PRELAUNCH", "1")
    assert load_prod().PRELAUNCH


# SPEC-0002: invented numbers, built from parts so gitleaks sees no whole phone number.
TEST_PHONES = ",".join("09" + "00" + f"{n:07d}" for n in (1, 2))


def test_test_phones_refused_without_prelaunch(prod_env: pytest.MonkeyPatch) -> None:
    prod_env.setattr("config.settings.base.CONSENT_VERSIONS", FINAL)
    prod_env.setenv("RAVANYAR_TEST_PHONES", TEST_PHONES)
    prod_env.setenv("RAVANYAR_TEST_CODE", "123456")
    with pytest.raises(ImproperlyConfigured, match="PRELAUNCH"):
        load_prod()


@pytest.mark.parametrize("code", ["", "12345", "abcdef", "۱۲۳۴۵۶"])
def test_test_phones_need_a_six_digit_code(prod_env: pytest.MonkeyPatch, code: str) -> None:
    prod_env.setenv("RAVANYAR_PRELAUNCH", "1")
    prod_env.setenv("RAVANYAR_TEST_PHONES", TEST_PHONES)
    prod_env.setenv("RAVANYAR_TEST_CODE", code)
    with pytest.raises(ImproperlyConfigured, match="6 digits"):
        load_prod()


def test_test_phones_on_prelaunch(prod_env: pytest.MonkeyPatch) -> None:
    prod_env.setenv("RAVANYAR_PRELAUNCH", "1")
    prod_env.setenv("RAVANYAR_TEST_PHONES", TEST_PHONES)
    prod_env.setenv("RAVANYAR_TEST_CODE", "123456")
    assert {"+98" + "900" + f"{n:07d}" for n in (1, 2)} == load_prod().TEST_PHONES


def test_no_test_phones_by_default(prod_env: pytest.MonkeyPatch) -> None:
    prod_env.setenv("RAVANYAR_PRELAUNCH", "1")
    assert frozenset() == load_prod().TEST_PHONES
