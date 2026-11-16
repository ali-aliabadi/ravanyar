"""Therapist availability and session booking (SPEC-0004). Thin views, as in `api.py`."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from django.http import HttpRequest
from ninja import Router, Schema, Status
from pydantic import AwareDatetime

from core import booking
from core.auth import current
from core.models import Booking, BookingStatus, Slot

router = Router()


class SlotOut(Schema):
    id: UUID
    start_at: datetime


class SlotIn(Schema):
    start_at: AwareDatetime  # a naive time is ambiguous: 422


class TherapistSlotOut(SlotOut):
    """The therapist's own slot. Booked or not, never by whom."""

    state: Literal["open", "booked", "cancelled"]


class BookIn(Schema):
    slot_id: UUID


class BookingOut(Schema):
    id: UUID
    therapist_id: UUID
    therapist_name: str
    start_at: datetime
    status: BookingStatus
    cancelled_by: str


def _booking_out(b: Booking) -> BookingOut:
    return BookingOut(
        id=b.pk,
        therapist_id=b.slot.therapist_id,
        therapist_name=b.slot.therapist.therapist_profile.display_name,
        start_at=b.slot.start_at,
        status=BookingStatus(b.status),
        cancelled_by=b.cancelled_by,
    )


def _slot_out(slot: Slot) -> TherapistSlotOut:
    return TherapistSlotOut(id=slot.pk, start_at=slot.start_at, state=slot.state)  # type: ignore[attr-defined]  # annotated in my_slots


@router.get("/therapists/{therapist_id}/slots", response=list[SlotOut])
def open_slots(request: HttpRequest, therapist_id: UUID) -> list[SlotOut]:
    return [SlotOut(id=s.pk, start_at=s.start_at) for s in booking.open_slots(therapist_id)]


@router.post("/bookings", response={201: BookingOut})
def book(request: HttpRequest, payload: BookIn) -> Status[BookingOut]:
    return Status(201, _booking_out(booking.book(current(request).account, payload.slot_id)))


@router.get("/me/bookings", response=list[BookingOut])
def my_bookings(request: HttpRequest) -> list[BookingOut]:
    return [_booking_out(b) for b in booking.my_bookings(current(request).account)]


@router.post("/bookings/{booking_id}/cancel", response=BookingOut)
def cancel_booking(request: HttpRequest, booking_id: UUID) -> BookingOut:
    return _booking_out(booking.cancel_as_client(current(request).account, booking_id))


@router.get("/therapist/slots", response=list[TherapistSlotOut])
def my_slots(request: HttpRequest) -> list[TherapistSlotOut]:
    return [_slot_out(s) for s in booking.my_slots(current(request).account)]


@router.post("/therapist/slots", response={201: TherapistSlotOut})
def add_slot(request: HttpRequest, payload: SlotIn) -> Status[TherapistSlotOut]:
    slot = booking.add_slot(current(request).account, payload.start_at)
    return Status(201, TherapistSlotOut(id=slot.pk, start_at=slot.start_at, state="open"))


@router.delete("/therapist/slots/{slot_id}", response={204: None})
def remove_slot(request: HttpRequest, slot_id: UUID) -> Status[None]:
    booking.remove_slot(current(request).account, slot_id)
    return Status(204, None)


@router.post("/therapist/slots/{slot_id}/cancel", response=TherapistSlotOut)
def cancel_session(request: HttpRequest, slot_id: UUID) -> TherapistSlotOut:
    return _slot_out(booking.cancel_as_therapist(current(request).account, slot_id))
