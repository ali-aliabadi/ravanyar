"""Therapist signup, credential upload, admin review and activation (SPEC-0003). Services."""

from uuid import UUID

from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from core.access import authorize, seal, unseal
from core.crypto import aad
from core.errors import (
    AccessDeniedError,
    BadFileError,
    IncompleteError,
    NotFoundError,
    WrongStateError,
)
from core.models import (
    Account,
    Credential,
    CredentialKind,
    Purpose,
    RejectReason,
    Review,
    Role,
    TherapistProfile,
)

MAX_BYTES = 5 * 1024 * 1024
# The file's own first bytes decide its type; the browser's claim is ignored.
MAGIC = {b"%PDF-": "application/pdf", b"\xff\xd8\xff": "image/jpeg", b"\x89PNG\r\n": "image/png"}
PUBLIC_FIELDS = ("display_name", "title", "bio", "specialties")
EDITABLE = (Review.DRAFT, Review.REJECTED, Review.APPROVED)


def require_role(account: Account, role: Role) -> None:
    if account.role != role:
        raise AccessDeniedError


def _location(credential: Credential) -> bytes:
    return aad("core_credential", "content", credential.pk)


def own_profile(account: Account) -> TherapistProfile:
    require_role(account, Role.THERAPIST)
    return TherapistProfile.objects.get_or_create(account=account)[0]


def credentials(account: Account) -> QuerySet[Credential]:
    return Credential.objects.filter(therapist=account).order_by("uploaded_at").defer("content_ct")


def update_profile(account: Account, changes: dict[str, object]) -> TherapistProfile:
    """Changing what clients read on an approved profile sends it back for review."""
    profile = own_profile(account)
    if profile.status not in EDITABLE:
        raise WrongStateError
    public_changed = any(
        getattr(profile, field) != changes[field] for field in PUBLIC_FIELDS if field in changes
    )
    for field, value in changes.items():
        setattr(profile, field, value)
    if profile.status == Review.APPROVED and public_changed:
        profile.status, profile.submitted_at = Review.SUBMITTED, timezone.now()
    profile.save()
    return profile


def add_credential(account: Account, kind: CredentialKind, data: bytes) -> Credential:
    profile = own_profile(account)
    if profile.status not in (Review.DRAFT, Review.REJECTED):
        raise WrongStateError
    mime = next((m for magic, m in MAGIC.items() if data.startswith(magic)), None)
    if mime is None or not 0 < len(data) <= MAX_BYTES:
        raise BadFileError
    credential = Credential(therapist=account, kind=kind, mime=mime, size=len(data))
    credential.content_ct = seal(account, _location(credential), data)
    credential.save()
    return credential


def delete_credential(account: Account, credential_id: UUID) -> None:
    profile = own_profile(account)
    if profile.status not in (Review.DRAFT, Review.REJECTED):
        raise WrongStateError
    if not Credential.objects.filter(pk=credential_id, therapist=account).delete()[0]:
        raise NotFoundError


def submit(account: Account) -> TherapistProfile:
    profile = own_profile(account)
    if profile.status not in (Review.DRAFT, Review.REJECTED):
        raise WrongStateError
    has_license = credentials(account).filter(kind=CredentialKind.LICENSE).exists()
    if not (profile.display_name and profile.title and profile.fee_rial and has_license):
        raise IncompleteError
    profile.status, profile.submitted_at = Review.SUBMITTED, timezone.now()
    profile.reject_reason = ""
    profile.save()
    return profile


def review_queue(admin: Account, status: Review) -> QuerySet[TherapistProfile]:
    require_role(admin, Role.ADMIN)
    return TherapistProfile.objects.filter(status=status).order_by("submitted_at")


def read_credential(actor: Account, credential_id: UUID) -> tuple[str, bytes]:
    """The therapist themself or an admin; every read, allowed or not, is in the access log."""
    credential = Credential.objects.select_related("therapist").filter(pk=credential_id).first()
    if credential is None:
        raise NotFoundError
    owner = credential.therapist
    grant = authorize(actor, owner, Purpose.CREDENTIALS)
    data = unseal(grant, owner, _location(credential), bytes(credential.content_ct))
    return credential.mime, data


def decide(admin: Account, therapist_id: UUID, reason: RejectReason | None) -> TherapistProfile:
    """Approve when `reason` is None, otherwise reject with it."""
    require_role(admin, Role.ADMIN)
    with transaction.atomic():
        profile = TherapistProfile.objects.select_for_update().filter(pk=therapist_id).first()
        if profile is None:
            raise NotFoundError
        if profile.status != Review.SUBMITTED:
            raise WrongStateError
        profile.status = Review.REJECTED if reason else Review.APPROVED
        profile.reject_reason = reason or ""
        profile.reviewed_at, profile.reviewed_by = timezone.now(), admin
        profile.save()
    return profile


def forget(account: Account) -> None:
    """Account deletion: the published text is plaintext, so it is blanked, not shredded."""
    TherapistProfile.objects.filter(account=account).update(
        display_name="", title="", bio="", specialties="", status=Review.DRAFT
    )
