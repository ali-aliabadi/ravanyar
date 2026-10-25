"""Persistence only (AGENTS.md §4). No column holds identifying data in plaintext (ADR 0004)."""

from uuid import uuid4

from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models


class Role(models.TextChoices):
    CLIENT = "client"
    THERAPIST = "therapist"
    ADMIN = "admin"


class Account(AbstractBaseUser):
    """A person. Deletion shreds the key and nulls the fields; the row stays as a tombstone."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    role = models.CharField(max_length=16, choices=Role.choices)
    is_active = models.BooleanField(default=True)
    # Phone under the account's data key; the data key under the master key.
    phone_ct = models.BinaryField(null=True)
    # NULL rather than "" so any number of deleted accounts fit under the unique constraint.
    phone_index = models.CharField(max_length=64, unique=True, null=True)  # noqa: DJ001
    wrapped_key = models.BinaryField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True)

    USERNAME_FIELD = "id"


class SignInCode(models.Model):
    phone_index = models.CharField(max_length=64, db_index=True)
    code_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    used_at = models.DateTimeField(null=True)

    def __str__(self) -> str:
        return str(self.pk)


class AuthSession(models.Model):
    token_hash = models.CharField(max_length=64, unique=True)
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="sessions")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True)

    def __str__(self) -> str:
        return str(self.pk)


class Document(models.TextChoices):
    TERMS = "terms"
    PRIVACY = "privacy"


class Consent(models.Model):
    """One grant. Withdrawal sets withdrawn_at; granting again adds a new row."""

    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="consents")
    document = models.CharField(max_length=32, choices=Document.choices)
    version = models.CharField(max_length=32)
    given_at = models.DateTimeField(auto_now_add=True)
    withdrawn_at = models.DateTimeField(null=True)

    def __str__(self) -> str:
        return str(self.pk)


class Purpose(models.TextChoices):
    PROFILE = "profile"
    CONSENTS = "consents"


class Decision(models.TextChoices):
    ALLOWED = "allowed"
    DENIED = "denied"


class AccessLog(models.Model):
    """Append-only: a trigger in migration 0002 rejects UPDATE, DELETE and TRUNCATE."""

    actor = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="+")
    subject = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="+")
    purpose = models.CharField(max_length=32, choices=Purpose.choices)
    decision = models.CharField(max_length=8, choices=Decision.choices)
    at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.pk)
