"""SPEC-0004: therapists choose specialties from a fixed list, up to five."""

from collections.abc import Callable
from typing import Any

import pytest
from django.test import Client

from core.models import Review, TherapistProfile
from core.tests.conftest import bearer, make_phone

pytestmark = [pytest.mark.integration, pytest.mark.django_db]
JSON = "application/json"


def put(token: str, specialties: list[str]) -> Any:
    body = {"display_name": "دکتر الف", "title": "روان‌شناس", "bio": "", "specialties": specialties}
    return Client().put("/api/therapist/profile", body, JSON, **bearer(token))


def test_profile_refuses_unknown_or_too_many(sign_in: Callable[..., str]) -> None:
    token = sign_in(make_phone(500), role="therapist")
    assert put(token, ["anxiety", "made-up-code"]).status_code == 422
    six = ["anxiety", "depression", "couples", "family", "child", "trauma"]
    assert put(token, six).status_code == 422
    response = put(token, ["anxiety", "grief", "anxiety"])
    assert response.status_code == 200
    assert response.json()["specialties"] == ["anxiety", "grief"]  # duplicates collapse


def test_specialty_change_needs_review(sign_in: Callable[..., str]) -> None:
    token = sign_in(make_phone(501), role="therapist")
    assert put(token, ["anxiety"]).status_code == 200
    TherapistProfile.objects.update(status=Review.APPROVED)
    assert put(token, ["anxiety"]).json()["status"] == "approved"  # unchanged: stays active
    assert put(token, ["anxiety", "sleep"]).json()["status"] == "submitted"
