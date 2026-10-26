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
