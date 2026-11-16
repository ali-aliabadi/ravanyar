"""Therapist verification and public profile (SPEC-0003). Persistence only."""

from uuid import uuid4

from django.db import models

from core.models.accounts import Account


class Review(models.TextChoices):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class RejectReason(models.TextChoices):
    """Fixed reasons, so a reviewer never types anything about the person into a column."""

    UNREADABLE = "unreadable"
    LICENSE_INVALID = "license_invalid"
    MISMATCH = "mismatch"
    INCOMPLETE = "incomplete"


class TherapistProfile(models.Model):
    """The text fields are the therapist's published profile: public data they write to be
    found, shown to clients only while approved. Deleting the account blanks them."""

    account = models.OneToOneField(
        Account, primary_key=True, on_delete=models.PROTECT, related_name="therapist_profile"
    )
    display_name = models.CharField(max_length=80, blank=True)
    title = models.CharField(max_length=80, blank=True)
    bio = models.TextField(max_length=2000, blank=True)
    specialties = models.CharField(max_length=200, blank=True)
    fee_rial = models.PositiveBigIntegerField(null=True)
    status = models.CharField(max_length=16, choices=Review.choices, default=Review.DRAFT)
    submitted_at = models.DateTimeField(null=True)
    reviewed_at = models.DateTimeField(null=True)
    reviewed_by = models.ForeignKey(Account, null=True, on_delete=models.PROTECT, related_name="+")
    reject_reason = models.CharField(max_length=32, choices=RejectReason.choices, blank=True)

    def __str__(self) -> str:
        return str(self.pk)


class CredentialKind(models.TextChoices):
    LICENSE = "license"
    DEGREE = "degree"
    NATIONAL_ID = "national_id"


class Credential(models.Model):
    """An uploaded document, encrypted under the therapist's data key."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    therapist = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="credentials")
    kind = models.CharField(max_length=16, choices=CredentialKind.choices)
    mime = models.CharField(max_length=32)
    size = models.PositiveIntegerField()
    content_ct = models.BinaryField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.pk)
