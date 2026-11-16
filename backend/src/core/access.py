"""The one place that decides whether an actor may read a person's data (SPEC-0001).

Every decision writes an access-log row. Decrypting needs the Grant that `authorize` returns,
so a read that skipped the check fails instead of passing quietly. Later specs add their
rules to `authorize` and nowhere else.
"""

from dataclasses import dataclass
from uuid import UUID

from core.crypto import aad, decrypt, encrypt, unwrap
from core.errors import AccessDeniedError
from core.models import AccessLog, Account, Booking, BookingStatus, Decision, Purpose, Role


@dataclass(frozen=True)
class Grant:
    actor_id: UUID
    subject_id: UUID
    purpose: Purpose


def _allowed(actor: Account, subject: Account, purpose: Purpose) -> bool:
    if actor.pk == subject.pk:
        return True
    if purpose == Purpose.CREDENTIALS:  # SPEC-0003: an admin reviews a therapist's documents
        return actor.role == Role.ADMIN and subject.role == Role.THERAPIST
    if purpose == Purpose.BOOKING:  # SPEC-0004: only while the client is booked with them
        return (
            actor.role == Role.THERAPIST
            and Booking.objects.filter(
                client=subject, slot__therapist=actor, status=BookingStatus.BOOKED
            ).exists()
        )
    return False


def authorize(actor: Account, subject: Account, purpose: Purpose) -> Grant:
    allowed = _allowed(actor, subject, purpose)
    AccessLog.objects.create(
        actor=actor,
        subject=subject,
        purpose=purpose,
        decision=Decision.ALLOWED if allowed else Decision.DENIED,
    )
    if not allowed:
        raise AccessDeniedError
    return Grant(actor.pk, subject.pk, purpose)


def read_phone(grant: Grant, account: Account) -> str:
    if grant.subject_id != account.pk or account.wrapped_key is None or account.phone_ct is None:
        raise AccessDeniedError
    key = unwrap(account.pk, bytes(account.wrapped_key))
    return decrypt(key, aad("core_account", "phone", account.pk), bytes(account.phone_ct)).decode()


def seal(owner: Account, location: bytes, plaintext: bytes) -> bytes:
    """Encrypt under the owner's data key. Writing needs no Grant; the caller checked the role."""
    if owner.wrapped_key is None:
        raise AccessDeniedError
    return encrypt(unwrap(owner.pk, bytes(owner.wrapped_key)), location, plaintext)


def unseal(grant: Grant, owner: Account, location: bytes, blob: bytes) -> bytes:
    if grant.subject_id != owner.pk or owner.wrapped_key is None:
        raise AccessDeniedError
    return decrypt(unwrap(owner.pk, bytes(owner.wrapped_key)), location, blob)


def name_location(account: Account) -> bytes:
    return aad("core_account", "name", account.pk)


def read_name(actor: Account, account: Account, purpose: Purpose) -> str:
    """SPEC-0004: a client's optional first name. Not set reads as "" and logs nothing."""
    if account.name_ct is None:
        return ""
    grant = authorize(actor, account, purpose)
    return unseal(grant, account, name_location(account), bytes(account.name_ct)).decode()
