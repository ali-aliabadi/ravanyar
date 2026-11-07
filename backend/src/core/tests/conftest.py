"""Integration tests get a real Postgres from testcontainers; unit tests never start one."""

from collections.abc import Callable, Iterator
from typing import Any

import pytest
from django.conf import settings
from django.test import Client
from django.test.utils import setup_databases
from testcontainers.community.postgres import PostgresContainer


@pytest.fixture(scope="session")
def django_db_setup(django_db_blocker: pytest.FixtureRequest) -> Iterator[None]:
    """Replace pytest-django's database with a throwaway container, migrations and all."""
    with PostgresContainer("postgres:17") as postgres:
        settings.DATABASES["default"] |= {
            "HOST": postgres.get_container_host_ip(),
            "PORT": str(postgres.get_exposed_port(5432)),
            "NAME": postgres.dbname,
            "USER": postgres.username,
            "PASSWORD": postgres.password,
        }
        with django_db_blocker.unblock():  # type: ignore[attr-defined]
            setup_databases(verbosity=0, interactive=False)
        yield


def make_phone(n: int) -> str:
    """An invented number. Built from parts so no whole number sits in the repo for gitleaks."""
    return "+98" + "912" + f"{n:07d}"


@pytest.fixture
def sent_codes(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Stand-in for Kavenegar: phone -> last code sent."""
    sent: dict[str, str] = {}
    monkeypatch.setattr("core.sms.send_code", lambda phone, code: sent.__setitem__(phone, code))
    return sent


@pytest.fixture
def sign_in(sent_codes: dict[str, str]) -> Callable[..., str]:
    """Run the real sign-in flow over HTTP and return the bearer token."""

    def run(phone: str, role: str = "client", client: Client | None = None) -> str:
        client = client or Client()
        sent = client.post("/api/auth/code", {"phone": phone}, "application/json")
        assert sent.status_code == 202
        body = {"phone": phone, "code": sent_codes[phone], "role": role, **CURRENT}
        response = client.post("/api/auth/verify", body, "application/json")
        assert response.status_code == 200, response.content
        token: str = response.json()["token"]
        return token

    return run


CURRENT = {
    "terms_version": settings.CONSENT_VERSIONS["terms"],
    "privacy_version": settings.CONSENT_VERSIONS["privacy"],
}


def bearer(token: str) -> dict[str, Any]:
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}
