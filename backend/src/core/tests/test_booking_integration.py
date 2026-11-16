"""SPEC-0004: therapists publish slots, clients book them, never twice."""

from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

import pytest
from django.db import IntegrityError, transaction
from django.test import Client
from django.utils import timezone

from core.models import Account, Booking, Review, Slot, TherapistProfile
from core.tests.conftest import bearer, make_phone

pytestmark = [pytest.mark.integration, pytest.mark.django_db]
JSON = "application/json"


def at(days: float = 3, hours: float = 0) -> datetime:
    return timezone.now() + timedelta(days=days, hours=hours)


def therapist(sign_in: Callable[..., str], n: int, approved: bool = True) -> str:
    token = sign_in(make_phone(n), role="therapist")
    account = Account.objects.get(role="therapist", therapist_profile__isnull=True)
    TherapistProfile.objects.create(
        account=account,
        display_name=f"دکتر {n}",
        status=Review.APPROVED if approved else Review.DRAFT,
    )
    return token


def add(token: str, when: datetime) -> Any:
    body = {"start_at": when.isoformat()}
    return Client().post("/api/therapist/slots", body, JSON, **bearer(token))


def book(token: str, slot_id: str) -> Any:
    return Client().post("/api/bookings", {"slot_id": slot_id}, JSON, **bearer(token))


def open_ids(token: str) -> list[str]:
    therapist_id = str(Slot.objects.values_list("therapist_id", flat=True).first())
    response = Client().get(f"/api/therapists/{therapist_id}/slots", **bearer(token))
    return [s["id"] for s in response.json()]


def test_therapist_adds_slots_within_rules(sign_in: Callable[..., str]) -> None:
    token = therapist(sign_in, 600)
    first = add(token, at(3))
    assert first.status_code == 201
    assert first.json()["state"] == "open"
    assert add(token, at(3, hours=0.5)).status_code == 422  # overlaps the first
    assert add(token, at(3, hours=1)).status_code == 201  # 60 minutes later is free
    assert add(token, at(-1)).status_code == 422  # past
    assert add(token, at(61)).status_code == 422  # beyond the horizon
    naive = {"start_at": "2030-01-01T10:00:00"}
    response = Client().post("/api/therapist/slots", naive, JSON, **bearer(token))
    assert response.status_code == 422


def test_unapproved_therapist_cannot_add_slots(sign_in: Callable[..., str]) -> None:
    assert add(therapist(sign_in, 601, approved=False), at(3)).status_code == 409


def test_client_sees_open_slots_only(sign_in: Callable[..., str]) -> None:
    token = therapist(sign_in, 602)
    soon = add(token, at(0, hours=0.5)).json()["id"]  # inside the one-hour lead
    later = add(token, at(3)).json()["id"]
    taken = add(token, at(4)).json()["id"]
    gone = add(token, at(5)).json()["id"]
    Client().delete(f"/api/therapist/slots/{gone}", **bearer(token))
    client = sign_in(make_phone(603))
    assert book(client, taken).status_code == 201
    assert open_ids(client) == [later]
    assert soon not in open_ids(client)
    TherapistProfile.objects.update(status=Review.SUBMITTED)
    therapist_id = Slot.objects.values_list("therapist_id", flat=True).first()
    assert (
        Client().get(f"/api/therapists/{therapist_id}/slots", **bearer(client)).status_code == 404
    )


def test_same_slot_cannot_be_booked_twice(sign_in: Callable[..., str]) -> None:
    slot_id = add(therapist(sign_in, 604), at(3)).json()["id"]
    first, second = sign_in(make_phone(605)), sign_in(make_phone(606))
    assert book(first, slot_id).status_code == 201
    assert book(second, slot_id).status_code == 409
    # Two requests that both passed the open-slot check: the database refuses the second.
    other = Account.objects.get(pk=Booking.objects.get().client_id)
    with pytest.raises(IntegrityError), transaction.atomic():
        Booking.objects.create(slot_id=slot_id, client=other)
    assert Booking.objects.count() == 1


def test_client_cancel_reopens_slot(sign_in: Callable[..., str]) -> None:
    slot_id = add(therapist(sign_in, 607), at(3)).json()["id"]
    client = sign_in(make_phone(608))
    booking_id = book(client, slot_id).json()["id"]
    response = Client().post(f"/api/bookings/{booking_id}/cancel", **bearer(client))
    assert (response.status_code, response.json()["cancelled_by"]) == (200, "client")
    assert open_ids(client) == [slot_id]
    again = book(client, slot_id).json()["id"]
    Slot.objects.update(start_at=at(-0.01))  # the session has started
    assert Client().post(f"/api/bookings/{again}/cancel", **bearer(client)).status_code == 409


def test_therapist_cancel_withdraws_slot(sign_in: Callable[..., str]) -> None:
    token = therapist(sign_in, 609)
    slot_id = add(token, at(3)).json()["id"]
    client = sign_in(make_phone(610))
    book(client, slot_id)
    assert Client().delete(f"/api/therapist/slots/{slot_id}", **bearer(token)).status_code == 409
    response = Client().post(f"/api/therapist/slots/{slot_id}/cancel", **bearer(token))
    assert (response.status_code, response.json()["state"]) == (200, "cancelled")
    mine = Client().get("/api/me/bookings", **bearer(client)).json()
    assert (mine[0]["status"], mine[0]["cancelled_by"]) == ("cancelled", "therapist")
    assert open_ids(client) == []


def test_roles_and_ownership(sign_in: Callable[..., str]) -> None:
    token = therapist(sign_in, 611)
    slot_id = add(token, at(3)).json()["id"]
    client, stranger = sign_in(make_phone(612)), sign_in(make_phone(613))
    assert book(token, slot_id).status_code == 403  # a therapist cannot book
    assert Client().get("/api/me/bookings", **bearer(token)).status_code == 403
    assert add(client, at(3)).status_code == 403  # a client cannot publish
    assert Client().get("/api/therapist/slots", **bearer(client)).status_code == 403
    booking_id = book(client, slot_id).json()["id"]
    cancel = f"/api/bookings/{booking_id}/cancel"
    assert Client().post(cancel, **bearer(stranger)).status_code == 404
    assert Client().get("/api/me/bookings", **bearer(stranger)).json() == []
    other = therapist(sign_in, 614)
    path = f"/api/therapist/slots/{slot_id}/cancel"
    assert Client().post(path, **bearer(other)).status_code == 404


def test_deletion_cancels_future_bookings(sign_in: Callable[..., str]) -> None:
    token = therapist(sign_in, 615)
    first, second = add(token, at(3)).json()["id"], add(token, at(4)).json()["id"]
    leaving, staying = sign_in(make_phone(616)), sign_in(make_phone(617))
    book(leaving, first)
    book(staying, second)
    assert Client().delete("/api/me", **bearer(leaving)).status_code == 204
    assert open_ids(staying) == [first]  # the deleted client's slot is open again
    assert Client().delete("/api/me", **bearer(token)).status_code == 204
    assert Booking.objects.get(slot_id=second).cancelled_by == "system"
    assert not Slot.objects.filter(withdrawn_at=None).exists()


def test_therapist_never_sees_client(sign_in: Callable[..., str]) -> None:
    token = therapist(sign_in, 618)
    slot_id = add(token, at(3)).json()["id"]
    client = sign_in(make_phone(619))
    book(client, slot_id)
    client_id = str(Account.objects.get(role="client").pk)
    slots = Client().get("/api/therapist/slots", **bearer(token))
    cancelled = Client().post(f"/api/therapist/slots/{slot_id}/cancel", **bearer(token))
    for response in (slots, cancelled):
        body = response.content.decode()
        assert client_id not in body
        assert make_phone(619)[3:] not in body
    assert slots.json()[0]["state"] == "booked"
