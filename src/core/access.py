"""The one place that decides whether an actor may read a person's data (SPEC-0001).

Every decision writes an access-log row. Decrypting needs the Grant that `authorize` returns,
so a read that skipped the check fails instead of passing quietly. Later specs add their
rules to `authorize` and nowhere else.
"""

from dataclasses import dataclass
from uuid import UUID

from core.crypto import aad, decrypt, unwrap
from core.errors import AccessDeniedError
from core.models import AccessLog, Account, Decision, Purpose


@dataclass(frozen=True)
class Grant:
    actor_id: UUID
    subject_id: UUID
    purpose: Purpose


def authorize(actor: Account, subject: Account, purpose: Purpose) -> Grant:
    allowed = actor.pk == subject.pk
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
