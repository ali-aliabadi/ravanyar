"""SPEC-0004: moving a booking, weekly slots, the client's first name, session reminders."""

import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from io import StringIO
from typing import Any

import pytest
from django.core.management import call_command
from django.test import Client
from django.test.utils import override_settings
from django.utils import timezone

from core.models import AccessLog, Account, Booking, Purpose, Review, TherapistProfile
from core.tests.conftest import bearer, make_phone

pytestmark = [pytest.mark.integration, pytest.mark.django_db]
JSON = "application/json"


def at(days: float = 3, hours: float = 0) -> datetime:
    return timezone.now() + timedelta(days=days, hours=hours)


def therapist(sign_in: Callable[..., str], n: int) -> str:
    token = sign_in(make_phone(n), role="therapist")
    account = Account.objects.get(role="therapist", therapist_profile__isnull=True)
    TherapistProfile.objects.create(account=account, display_name="دکتر", status=Review.APPROVED)
    return token


def post(path: str, token: str, body: dict[str, Any] | None = None) -> Any:
    return Client().post(path, body or {}, JSON, **bearer(token))


def slot(token: str, when: datetime) -> str:
    response = post("/api/therapist/slots", token, {"start_at": when.isoformat()})
    assert response.status_code == 201, response.content
    slot_id: str = response.json()["id"]
    return slot_id


def test_client_moves_booking(sign_in: Callable[..., str]) -> None:
    token = therapist(sign_in, 700)
    first, second, other = slot(token, at(3)), slot(token, at(4)), slot(token, at(5))
    client, rival = sign_in(make_phone(701)), sign_in(make_phone(702))
    booking_id = post("/api/bookings", client, {"slot_id": first}).json()["id"]
    post("/api/bookings", rival, {"slot_id": other})
    move = f"/api/bookings/{booking_id}/move"
    assert post(move, client, {"slot_id": other}).status_code == 409  # taken: nothing changes
    assert Booking.objects.get(pk=booking_id).status == "booked"
    moved = post(move, client, {"slot_id": second})
    assert (moved.status_code, moved.json()["start_at"][:10]) == (200, at(4).isoformat()[:10])
    assert Booking.objects.get(pk=booking_id).status == "moved"
    assert post(f"/api/bookings/{booking_id}/move", client, {"slot_id": first}).status_code == 409
    profile = TherapistProfile.objects.get()
    free = Client().get(f"/api/therapists/{profile.pk}/slots", **bearer(client))
    assert [s["id"] for s in free.json()] == [first]  # the old time is open again


def test_weekly_slots_skip_what_does_not_fit(sign_in: Callable[..., str]) -> None:
    token = therapist(sign_in, 703)
    slot(token, at(3 + 7))  # week two is taken already
    body = {"start_at": at(3).isoformat(), "weeks": 4}
    response = post("/api/therapist/slots/weekly", token, body)
    assert response.status_code == 201
    assert (len(response.json()["created"]), response.json()["skipped"]) == (3, 1)
    far = {"start_at": at(58).isoformat(), "weeks": 2}  # week two passes the 60-day horizon
    assert post("/api/therapist/slots/weekly", token, far).json()["skipped"] == 1
    assert post("/api/therapist/slots/weekly", token, {**body, "weeks": 9}).status_code == 422
    assert post("/api/therapist/slots/weekly", token, body).status_code == 422  # nothing fits


def test_therapist_sees_first_name_of_booked_client_only(sign_in: Callable[..., str]) -> None:
    token = therapist(sign_in, 704)
    slot_id = slot(token, at(3))
    client = sign_in(make_phone(705))
    response = Client().put("/api/me/name", {"name": "  مریم "}, JSON, **bearer(client))
    assert response.status_code == 204
    assert Client().get("/api/me", **bearer(client)).json()["name"] == "مریم"
    stored = bytes(Account.objects.get(role="client").name_ct or b"")
    assert "مریم".encode() not in stored  # ciphertext under the client's key
    booking_id = post("/api/bookings", client, {"slot_id": slot_id}).json()["id"]
    slots = Client().get("/api/therapist/slots", **bearer(token)).json()
    assert slots[0]["client_name"] == "مریم"
    log = AccessLog.objects.get(purpose=Purpose.BOOKING)
    assert (log.actor_id, log.decision) == (Account.objects.get(role="therapist").pk, "allowed")
    post(f"/api/bookings/{booking_id}/cancel", client)
    assert Client().get("/api/therapist/slots", **bearer(token)).json()[0]["client_name"] == ""


def test_deleting_client_drops_name(sign_in: Callable[..., str]) -> None:
    client = sign_in(make_phone(706))
    Client().put("/api/me/name", {"name": "علی"}, JSON, **bearer(client))
    Client().delete("/api/me", **bearer(client))
    assert Account.objects.get().name_ct is None


def test_reminders_like_sign_in_codes(
    sign_in: Callable[..., str],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    token = therapist(sign_in, 707)
    real_slot, test_slot, later = slot(token, at(0, 5)), slot(token, at(0, 6)), slot(token, at(3))
    real, test = make_phone(708), make_phone(709)
    post("/api/bookings", sign_in(real), {"slot_id": real_slot})
    post("/api/bookings", sign_in(test), {"slot_id": test_slot})
    post("/api/bookings", sign_in(make_phone(710)), {"slot_id": later})  # 3 days out: not due
    sent: list[tuple[str, str, str]] = []
    monkeypatch.setattr(
        "core.sms.send_reminder", lambda phone, day, time: sent.append((phone, day, time))
    )
    caplog.set_level(logging.WARNING, logger="core.reminders")
    with override_settings(TEST_PHONES=frozenset({test})):  # as at sign-in: no SMS, a log line
        call_command("send_reminders", stdout=StringIO())
        call_command("send_reminders", stdout=StringIO())  # a reminded booking is skipped
    assert [phone for phone, _, _ in sent] == [real]
    weekday, time = sent[0][1:]
    assert weekday.endswith("شنبه") or weekday == "جمعه"
    assert len(time) == 5 and time[2] == ":"
    assert "staging test reminder" in caplog.text
    assert real[3:] not in caplog.text and test[3:] not in caplog.text
    assert AccessLog.objects.filter(purpose=Purpose.REMINDER).count() == 2
    assert Booking.objects.filter(reminded_at__isnull=False).count() == 2
