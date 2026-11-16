"""Therapist availability and session booking (SPEC-0004). Services.

A booking says a person is in therapy: nothing returned to a therapist carries the client.
"""

from datetime import datetime, timedelta
from uuid import UUID

from django.db import IntegrityError, transaction
from django.db.models import Case, CharField, Exists, OuterRef, Q, QuerySet, Value, When
from django.utils import timezone

from core import search
from core.access import read_name
from core.errors import BadTimeError, NotFoundError, WrongStateError
from core.models import (
    Account,
    Booking,
    BookingStatus,
    Party,
    Purpose,
    Review,
    Role,
    Slot,
    TherapistProfile,
)
from core.verification import require_role

SESSION = timedelta(minutes=50)
LEAD = timedelta(hours=1)  # a client books at least this far ahead
HORIZON = timedelta(days=60)  # a therapist publishes at most this far ahead
MAX_WEEKS = 8
WEEK = timedelta(days=7)  # Iran has had no daylight saving since 2022: a week is 168 hours


def _active_booking() -> Exists:
    return Exists(Booking.objects.filter(slot=OuterRef("pk"), status=BookingStatus.BOOKED))


def _bookable() -> QuerySet[Slot]:
    return Slot.objects.filter(
        withdrawn_at=None,
        start_at__gte=timezone.now() + LEAD,
        therapist__is_active=True,
        therapist__therapist_profile__status=Review.APPROVED,
    ).exclude(_active_booking())


def _lock_approved(therapist: Account) -> None:
    """The profile row lock serialises one therapist's concurrent adds, so overlap checks hold."""
    require_role(therapist, Role.THERAPIST)
    profile = TherapistProfile.objects.select_for_update().filter(account=therapist).first()
    if profile is None or profile.status != Review.APPROVED:
        raise WrongStateError


def _fits(therapist: Account, start_at: datetime) -> bool:
    now = timezone.now()
    near = Slot.objects.filter(
        therapist=therapist,
        withdrawn_at=None,
        start_at__gt=start_at - SESSION,
        start_at__lt=start_at + SESSION,
    )
    return now < start_at <= now + HORIZON and not near.exists()


@transaction.atomic
def add_slot(therapist: Account, start_at: datetime) -> Slot:
    _lock_approved(therapist)
    if not _fits(therapist, start_at):
        raise BadTimeError
    return Slot.objects.create(therapist=therapist, start_at=start_at)


@transaction.atomic
def add_weekly(therapist: Account, start_at: datetime, weeks: int) -> tuple[list[Slot], int]:
    """The same time on each of `weeks` weeks. A week that overlaps or passes the horizon is
    skipped and counted; nothing fitting at all is a bad time."""
    _lock_approved(therapist)
    if not 1 <= weeks <= MAX_WEEKS:
        raise BadTimeError
    made = []
    for start in (start_at + i * WEEK for i in range(weeks)):
        if _fits(therapist, start):
            made.append(Slot.objects.create(therapist=therapist, start_at=start))
    if not made:
        raise BadTimeError
    return made, weeks - len(made)


@transaction.atomic
def remove_slot(therapist: Account, slot_id: UUID) -> None:
    require_role(therapist, Role.THERAPIST)
    slot = (
        Slot.objects.select_for_update()
        .filter(pk=slot_id, therapist=therapist, withdrawn_at=None)
        .first()
    )
    if slot is None:
        raise NotFoundError
    if slot.bookings.filter(status=BookingStatus.BOOKED).exists():
        raise WrongStateError  # cancel the session instead
    slot.withdrawn_at = timezone.now()
    slot.save(update_fields=["withdrawn_at"])


def open_slots(therapist_id: UUID) -> QuerySet[Slot]:
    """404 unless the therapist is approved, as their public profile is."""
    search.public_profile(therapist_id)
    return _bookable().filter(therapist_id=therapist_id).order_by("start_at")


def book(client: Account, slot_id: UUID) -> Booking:
    require_role(client, Role.CLIENT)
    try:
        with transaction.atomic():
            slot = _bookable().select_for_update(of=("self",)).filter(pk=slot_id).first()
            if slot is None:
                raise WrongStateError if Slot.objects.filter(pk=slot_id).exists() else NotFoundError
            return Booking.objects.create(slot=slot, client=client)
    except IntegrityError:  # another client's booking committed first
        raise WrongStateError from None


def move(client: Account, booking_id: UUID, slot_id: UUID) -> Booking:
    """Book the new slot and release the old one, or neither: the old time is never lost."""
    require_role(client, Role.CLIENT)
    try:
        with transaction.atomic():
            old = (
                Booking.objects.select_for_update(of=("self",))
                .select_related("slot")
                .filter(pk=booking_id, client=client)
                .first()
            )
            if old is None:
                raise NotFoundError
            if old.status != BookingStatus.BOOKED or old.slot.start_at <= timezone.now():
                raise WrongStateError
            slot = (
                _bookable()
                .select_for_update(of=("self",))
                .filter(pk=slot_id, therapist_id=old.slot.therapist_id)
                .first()
            )
            if slot is None:
                raise WrongStateError
            old.status, old.cancelled_by = BookingStatus.MOVED, Party.CLIENT
            old.cancelled_at = timezone.now()
            old.save(update_fields=["status", "cancelled_by", "cancelled_at"])
            return Booking.objects.create(slot=slot, client=client)
    except IntegrityError:  # another client took the new slot first
        raise WrongStateError from None


def _cancel(booking: Booking, by: Party) -> None:
    booking.status, booking.cancelled_by = BookingStatus.CANCELLED, by
    booking.cancelled_at = timezone.now()
    booking.save(update_fields=["status", "cancelled_by", "cancelled_at"])


@transaction.atomic
def cancel_as_client(client: Account, booking_id: UUID) -> Booking:
    """The slot opens again by itself: it has no active booking left."""
    require_role(client, Role.CLIENT)
    booking = (
        Booking.objects.select_for_update(of=("self",))
        .select_related("slot__therapist__therapist_profile")
        .filter(pk=booking_id, client=client)
        .first()
    )
    if booking is None:
        raise NotFoundError
    if booking.status != BookingStatus.BOOKED or booking.slot.start_at <= timezone.now():
        raise WrongStateError
    _cancel(booking, Party.CLIENT)
    return booking


@transaction.atomic
def cancel_as_therapist(therapist: Account, slot_id: UUID) -> Slot:
    """The therapist is not free after all: the slot is withdrawn, not offered again."""
    require_role(therapist, Role.THERAPIST)
    slot = (
        Slot.objects.select_for_update()
        .filter(pk=slot_id, therapist=therapist, withdrawn_at=None)
        .first()
    )
    if slot is None:
        raise NotFoundError
    booking = slot.bookings.filter(status=BookingStatus.BOOKED).first()
    if booking is None or slot.start_at <= timezone.now():
        raise WrongStateError
    _cancel(booking, Party.THERAPIST)
    slot.withdrawn_at = timezone.now()
    slot.save(update_fields=["withdrawn_at"])
    return my_slots(therapist).get(pk=slot.pk)


def my_bookings(client: Account) -> QuerySet[Booking]:
    require_role(client, Role.CLIENT)
    return (
        Booking.objects.filter(client=client)
        .select_related("slot__therapist__therapist_profile")
        .order_by("-slot__start_at")
    )


def my_slots(therapist: Account) -> QuerySet[Slot]:
    """Upcoming slots and their state; a withdrawn one shows only if a session was cancelled.
    Never who booked."""
    require_role(therapist, Role.THERAPIST)
    had_booking = Exists(Booking.objects.filter(slot=OuterRef("pk")))
    return (
        Slot.objects.filter(therapist=therapist, start_at__gte=timezone.now())
        .filter(Q(withdrawn_at=None) | Q(had_booking))
        .annotate(
            state=Case(
                When(_active_booking(), then=Value("booked")),
                When(withdrawn_at__isnull=False, then=Value("cancelled")),
                default=Value("open"),
                output_field=CharField(),
            )
        )
        .order_by("start_at")
    )


def client_names(therapist: Account, slots: list[Slot]) -> dict[UUID, str]:
    """First names of the clients booked into these slots, each read access-logged. A client
    who gave no name is not read and not logged."""
    booked = Booking.objects.filter(
        slot__in=[s.pk for s in slots], slot__therapist=therapist, status=BookingStatus.BOOKED
    ).select_related("client")
    names = {b.slot_id: read_name(therapist, b.client, Purpose.BOOKING) for b in booked}
    return {slot_id: name for slot_id, name in names.items() if name}


def forget(account: Account) -> None:
    """Account deletion: future sessions on either side are cancelled, the slots withdrawn."""
    now = timezone.now()
    Booking.objects.filter(
        Q(client=account) | Q(slot__therapist=account),
        status=BookingStatus.BOOKED,
        slot__start_at__gt=now,
    ).update(status=BookingStatus.CANCELLED, cancelled_by=Party.SYSTEM, cancelled_at=now)
    Slot.objects.filter(therapist=account, withdrawn_at=None, start_at__gt=now).update(
        withdrawn_at=now
    )
