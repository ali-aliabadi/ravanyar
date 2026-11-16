"""Therapist slots and session bookings (SPEC-0004). Persistence only."""

from uuid import uuid4

from django.db import models
from django.db.models import Q

from core.models.accounts import Account


class BookingStatus(models.TextChoices):
    BOOKED = "booked"
    CANCELLED = "cancelled"


class Party(models.TextChoices):
    CLIENT = "client"
    THERAPIST = "therapist"
    SYSTEM = "system"  # account deletion


class Slot(models.Model):
    """One session time a therapist published. Withdrawn, never deleted: bookings point here."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    therapist = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="slots")
    start_at = models.DateTimeField()
    withdrawn_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = (models.Index(fields=["therapist", "start_at"]),)

    def __str__(self) -> str:
        return str(self.pk)


class Booking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    slot = models.ForeignKey(Slot, on_delete=models.PROTECT, related_name="bookings")
    client = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="bookings")
    status = models.CharField(
        max_length=16, choices=BookingStatus.choices, default=BookingStatus.BOOKED
    )
    cancelled_by = models.CharField(max_length=16, choices=Party.choices, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True)

    class Meta:
        # The double-booking guarantee: Postgres holds it, not a check-then-insert.
        constraints = (
            models.UniqueConstraint(
                fields=["slot"],
                condition=Q(status="booked"),
                name="one_active_booking_per_slot",
            ),
        )

    def __str__(self) -> str:
        return str(self.pk)
