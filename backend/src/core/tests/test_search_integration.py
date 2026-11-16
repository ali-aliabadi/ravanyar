"""SPEC-0004: clients find approved therapists; nothing else is found, nothing is logged."""

import logging
from collections.abc import Callable
from typing import Any
from uuid import uuid4

import pytest
from django.test import Client
from django.utils import timezone

from core.models import Account, Review, Role, TherapistProfile
from core.tests.conftest import bearer, make_phone

pytestmark = [pytest.mark.integration, pytest.mark.django_db]
JSON = "application/json"
PUBLIC = {"id", "display_name", "title", "specialties", "bio", "fee_rial"}


def profile(status: Review = Review.APPROVED, active: bool = True, **text: str) -> TherapistProfile:
    account = Account.objects.create(role=Role.THERAPIST, is_active=active)
    fields = {"display_name": "دکتر نمونه", "title": "روان‌شناس", "specialties": "", **text}
    return TherapistProfile.objects.create(
        account=account, status=status, fee_rial=9_000_000, reviewed_at=timezone.now(), **fields
    )


def find(token: str, q: str = "") -> list[dict[str, Any]]:
    response = Client().post("/api/therapists/search", {"q": q}, JSON, **bearer(token))
    assert response.status_code == 200, response.content
    items: list[dict[str, Any]] = response.json()["items"]
    return items


def test_only_approved_profiles_are_found(sign_in: Callable[..., str]) -> None:
    approved = profile()
    for status in (Review.DRAFT, Review.SUBMITTED, Review.REJECTED):
        profile(status)
    profile(active=False)
    found = find(sign_in(make_phone(400)))
    assert [p["id"] for p in found] == [str(approved.pk)]
    assert set(found[0]) == PUBLIC


def test_search_matches_letter_variants_and_half_spaces(sign_in: Callable[..., str]) -> None:
    token = sign_in(make_phone(401))
    anxiety = profile(title="روان‌شناس بالینی", specialties="اضطراب، افسردگی")
    child = profile(title="مشاور", specialties="كودك")  # typed with Arabic kaf

    def ids(q: str) -> set[str]:
        return {p["id"] for p in find(token, q)}

    assert ids("روانشناس") == {str(anxiety.pk)}  # no half-space in the query
    assert ids("افسردگي") == {str(anxiety.pk)}  # Arabic yeh in the query
    assert ids("کودک") == {str(child.pk)}  # Persian kaf in the query
    assert ids("نامرتبط") == set()


def test_profile_leaves_search_when_not_approved(sign_in: Callable[..., str]) -> None:
    client_token = sign_in(make_phone(402))
    token = sign_in(make_phone(403), role="therapist")
    client = Client()
    body = {"display_name": "دکتر الف", "title": "روان‌شناس", "bio": "", "specialties": ""}
    assert client.put("/api/therapist/profile", body, JSON, **bearer(token)).status_code == 200
    TherapistProfile.objects.update(status=Review.APPROVED, fee_rial=9_000_000)
    assert len(find(client_token)) == 1
    body["bio"] = "متن تازه"  # changes what clients read, so back to review
    assert client.put("/api/therapist/profile", body, JSON, **bearer(token)).status_code == 200
    assert find(client_token) == []
    TherapistProfile.objects.update(status=Review.APPROVED)
    assert client.delete("/api/me", **bearer(token)).status_code == 204
    assert find(client_token) == []


def test_public_profile_hides_unapproved(sign_in: Callable[..., str]) -> None:
    token, client = sign_in(make_phone(404)), Client()
    shown, hidden = profile(bio="معرفی"), profile(Review.SUBMITTED)
    response = client.get(f"/api/therapists/{shown.pk}", **bearer(token))
    assert response.status_code == 200
    assert set(response.json()) == PUBLIC
    for therapist_id in (hidden.pk, uuid4()):
        response = client.get(f"/api/therapists/{therapist_id}", **bearer(token))
        assert (response.status_code, response.json()) == (404, {"detail": "not_found"})


def test_search_text_is_not_logged(
    sign_in: Callable[..., str], caplog: pytest.LogCaptureFixture
) -> None:
    token = sign_in(make_phone(405))
    caplog.set_level(logging.DEBUG)
    find(token, "افکار خودکشی")
    response = Client().post("/api/therapists/search", {"q": "x" * 101}, JSON, **bearer(token))
    assert response.status_code == 422  # rejected input is not echoed back either
    assert "خودکشی" not in caplog.text
    assert "x" * 101 not in caplog.text + response.content.decode()
