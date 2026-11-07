"""Sign-in, sessions, consent and account deletion (SPEC-0001). Views call one function each."""

import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from core import sms
from core.access import authorize, read_phone
from core.crypto import aad, blind_index, encrypt, new_data_key, wrap
from core.errors import (
    CodeRejectedError,
    OutdatedVersionError,
    RateLimitedError,
    SmsUnavailableError,
)
from core.models import Account, AuthSession, Consent, Document, Purpose, Role, SignInCode

CODE_TTL = timedelta(minutes=2)
CODE_PURGE_AFTER = timedelta(hours=24)
MAX_ATTEMPTS = 5
RESEND_AFTER = timedelta(seconds=60)
CODES_PER_HOUR = 5
SESSION_TTL = timedelta(days=30)


def _code_hash(phone_index: str, code: str) -> str:
    return blind_index(f"code:{phone_index}:{code}")


def token_hash(token: str) -> str:
    """256 random bits: an unkeyed hash is enough, unlike a phone number's."""
    return hashlib.sha256(token.encode()).hexdigest()


def request_code(phone: str) -> None:
    """Same outcome whether or not an account exists, so the response enumerates nobody."""
    now = timezone.now()
    # ponytail: purge rides on traffic, so a quiet day keeps rows longer; cron if that matters.
    SignInCode.objects.filter(created_at__lt=now - CODE_PURGE_AFTER).delete()
    index = blind_index(phone)
    recent = SignInCode.objects.filter(phone_index=index, created_at__gte=now - timedelta(hours=1))
    # ponytail: count-then-insert, two concurrent requests can both pass; lock if abused.
    if recent.count() >= CODES_PER_HOUR or recent.filter(created_at__gte=now - RESEND_AFTER):
        raise RateLimitedError
    code = f"{secrets.randbelow(10**6):06d}"
    row = SignInCode.objects.create(
        phone_index=index, code_hash=_code_hash(index, code), expires_at=now + CODE_TTL
    )
    try:
        sms.send_code(phone, code)
    except SmsUnavailableError:
        row.delete()
        raise


def verify_code(phone: str, code: str, role: Role, terms: str, privacy: str) -> str:
    """Check the latest code; on success create the account if new, record consent, return a
    session token. A wrong guess is counted even though the request fails."""
    current = settings.CONSENT_VERSIONS
    if (terms, privacy) != (current[Document.TERMS], current[Document.PRIVACY]):
        raise OutdatedVersionError
    now = timezone.now()
    index = blind_index(phone)
    token = None
    with transaction.atomic():
        challenge = (
            SignInCode.objects.select_for_update()
            .filter(phone_index=index, used_at=None)
            .order_by("-created_at")
            .first()
        )
        if challenge is None or challenge.expires_at <= now or challenge.attempts >= MAX_ATTEMPTS:
            raise CodeRejectedError
        if hmac.compare_digest(challenge.code_hash, _code_hash(index, code)):
            challenge.used_at = now
            account = Account.objects.filter(phone_index=index).first() or _create(phone, role)
            grant_consent(account, Document.TERMS, terms)
            grant_consent(account, Document.PRIVACY, privacy)
            token = _new_session(account)
        else:
            challenge.attempts += 1
        challenge.save(update_fields=["used_at", "attempts"])
    if token is None:
        raise CodeRejectedError
    return token


def _create(phone: str, role: Role) -> Account:
    account = Account(role=role, phone_index=blind_index(phone))
    data_key = new_data_key()
    account.wrapped_key = wrap(account.pk, data_key)
    account.phone_ct = encrypt(data_key, aad("core_account", "phone", account.pk), phone.encode())
    account.set_unusable_password()
    account.save()
    return account


def _new_session(account: Account) -> str:
    token = secrets.token_urlsafe(32)
    AuthSession.objects.create(
        token_hash=token_hash(token), account=account, expires_at=timezone.now() + SESSION_TTL
    )
    return token


def logout(session: AuthSession) -> None:
    session.revoked_at = timezone.now()
    session.save(update_fields=["revoked_at"])


def profile_phone(account: Account) -> str:
    return read_phone(authorize(account, account, Purpose.PROFILE), account)


def delete_account(account: Account) -> None:
    """Crypto-shred: without the wrapped key every ciphertext of this person is noise."""
    now = timezone.now()
    with transaction.atomic():
        if account.phone_index:
            SignInCode.objects.filter(phone_index=account.phone_index).delete()
        Account.objects.filter(pk=account.pk).update(
            wrapped_key=None, phone_ct=None, phone_index=None, is_active=False, deleted_at=now
        )
        AuthSession.objects.filter(account=account, revoked_at=None).update(revoked_at=now)


def has_current_consent(account: Account) -> bool:
    active = Consent.objects.filter(account=account, withdrawn_at=None)
    given = set(active.values_list("document", "version"))
    return all(pair in given for pair in settings.CONSENT_VERSIONS.items())


def list_consents(account: Account) -> QuerySet[Consent]:
    authorize(account, account, Purpose.CONSENTS)
    return Consent.objects.filter(account=account).order_by("given_at", "id")


def grant_consent(account: Account, document: Document, version: str) -> None:
    if settings.CONSENT_VERSIONS.get(document) != version:
        raise OutdatedVersionError
    active = Consent.objects.filter(account=account, document=document, withdrawn_at=None)
    if not active.filter(version=version).exists():
        active.update(withdrawn_at=timezone.now())  # an older version is superseded
        Consent.objects.create(account=account, document=document, version=version)


def withdraw_consent(account: Account, document: Document) -> None:
    Consent.objects.filter(account=account, document=document, withdrawn_at=None).update(
        withdrawn_at=timezone.now()
    )
