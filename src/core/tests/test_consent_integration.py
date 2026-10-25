from collections.abc import Callable

import pytest
from django.test import Client, override_settings

from core.models import Consent
from core.tests.conftest import CURRENT, bearer, make_phone

pytestmark = [pytest.mark.integration, pytest.mark.django_db]
JSON = "application/json"


def test_list_consents(sign_in: Callable[..., str]) -> None:
    response = Client().get("/api/me/consents", **bearer(sign_in(make_phone(30))))
    assert response.status_code == 200
    rows = response.json()
    assert {(r["document"], r["version"]) for r in rows} == {
        ("terms", CURRENT["terms_version"]),
        ("privacy", CURRENT["privacy_version"]),
    }
    assert all(r["given_at"] and r["withdrawn_at"] is None for r in rows)


def test_withdrawn_or_outdated_consent_blocks(sign_in: Callable[..., str]) -> None:
    client, auth = Client(), bearer(sign_in(make_phone(31)))
    assert client.post("/api/me/consents/privacy/withdraw", **auth).status_code == 204
    blocked = client.get("/api/me", **auth)
    assert (blocked.status_code, blocked.json()) == (403, {"detail": "consent_required"})
    # Still reachable without consent: the consent endpoints, logout, deletion.
    assert client.get("/api/me/consents", **auth).status_code == 200

    body = {"document": "privacy", "version": CURRENT["privacy_version"]}
    assert client.post("/api/me/consents", body, JSON, **auth).status_code == 201
    assert client.get("/api/me", **auth).status_code == 200

    with override_settings(CONSENT_VERSIONS={"terms": "terms-2", "privacy": "privacy-2"}):
        assert client.get("/api/me", **auth).status_code == 403  # a new version needs accepting


def test_regrant_adds_row(sign_in: Callable[..., str]) -> None:
    client, auth = Client(), bearer(sign_in(make_phone(32)))
    client.post("/api/me/consents/terms/withdraw", **auth)
    body = {"document": "terms", "version": CURRENT["terms_version"]}
    client.post("/api/me/consents", body, JSON, **auth)
    old, new = Consent.objects.filter(document="terms").order_by("given_at", "id")
    assert old.withdrawn_at is not None
    assert new.withdrawn_at is None


def test_grant_of_unknown_version_rejected(sign_in: Callable[..., str]) -> None:
    client, auth = Client(), bearer(sign_in(make_phone(33)))
    body = {"document": "terms", "version": "terms-0"}
    assert client.post("/api/me/consents", body, JSON, **auth).status_code == 422
