"""The one place that decides whether an actor may read a person's data (SPEC-0001).

Every decision writes an access-log row. Decrypting needs the Grant that `authorize` returns,
so a read that skipped the check fails instead of passing quietly. Later specs add their
rules to `authorize` and nowhere else.
"""

from dataclasses import dataclass
from uuid import UUID

from core.crypto import aad, decrypt, encrypt, unwrap
from core.errors import AccessDeniedError
from core.models import AccessLog, Account, Decision, Purpose, Role


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
