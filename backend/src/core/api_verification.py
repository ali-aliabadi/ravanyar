"""Therapist profile, credentials and admin review (SPEC-0003). Thin views, as in `api.py`."""

from datetime import datetime
from uuid import UUID

from django.http import HttpRequest, HttpResponse
from ninja import File, Form, Router, Schema, Status
from ninja.files import UploadedFile
from pydantic import Field

from core import verification
from core.auth import current
from core.models import CredentialKind, RejectReason, Review, TherapistProfile

router = Router()


class ProfileIn(Schema):
    display_name: str = Field(max_length=80)
    title: str = Field(max_length=80)
    bio: str = Field(max_length=2000)
    specialties: str = Field(max_length=200)
    fee_rial: int | None = Field(default=None, ge=10_000, le=1_000_000_000)


class CredentialOut(Schema):
    id: UUID
    kind: CredentialKind
    mime: str
    size: int
    uploaded_at: datetime


class ProfileOut(ProfileIn):
    id: UUID
    status: Review
    reject_reason: str
    submitted_at: datetime | None
    credentials: list[CredentialOut]


class DecisionIn(Schema):
    approve: bool
    reason: RejectReason | None = None


def _out(profile: TherapistProfile) -> ProfileOut:
    creds = verification.credentials(profile.account)
    return ProfileOut(
        id=profile.pk,
        display_name=profile.display_name,
        title=profile.title,
        bio=profile.bio,
        specialties=profile.specialties,
        fee_rial=profile.fee_rial,
        status=Review(profile.status),
        reject_reason=profile.reject_reason,
        submitted_at=profile.submitted_at,
        credentials=[CredentialOut.model_validate(c, from_attributes=True) for c in creds],
    )


@router.get("/therapist/profile", response=ProfileOut)
def get_profile(request: HttpRequest) -> ProfileOut:
    return _out(verification.own_profile(current(request).account))


@router.put("/therapist/profile", response=ProfileOut)
def put_profile(request: HttpRequest, payload: ProfileIn) -> ProfileOut:
    account = current(request).account
    return _out(verification.update_profile(account, payload.model_dump()))


@router.post("/therapist/credentials", response={201: CredentialOut})
def upload_credential(
    request: HttpRequest, kind: Form[CredentialKind], file: File[UploadedFile]
) -> Status[CredentialOut]:
    credential = verification.add_credential(current(request).account, kind, file.read())
    return Status(201, CredentialOut.model_validate(credential, from_attributes=True))


@router.delete("/therapist/credentials/{credential_id}", response={204: None})
def delete_credential(request: HttpRequest, credential_id: UUID) -> Status[None]:
    verification.delete_credential(current(request).account, credential_id)
    return Status(204, None)


@router.post("/therapist/submit", response=ProfileOut)
def submit(request: HttpRequest) -> ProfileOut:
    return _out(verification.submit(current(request).account))


@router.get("/credentials/{credential_id}")
def read_credential(request: HttpRequest, credential_id: UUID) -> HttpResponse:
    """The file itself, for its owner or an admin. Served as a download, never rendered."""
    mime, data = verification.read_credential(current(request).account, credential_id)
    response = HttpResponse(data, content_type=mime)
    response["Content-Disposition"] = "attachment"
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "no-store"
    return response


@router.get("/admin/therapists", response=list[ProfileOut])
def review_queue(request: HttpRequest, status: Review = Review.SUBMITTED) -> list[ProfileOut]:
    queue = verification.review_queue(current(request).account, status)
    return [_out(p) for p in queue.select_related("account")]


@router.post("/admin/therapists/{therapist_id}/decision", response=ProfileOut)
def decide(request: HttpRequest, therapist_id: UUID, payload: DecisionIn) -> ProfileOut:
    reason = None if payload.approve else payload.reason or RejectReason.INCOMPLETE
    return _out(verification.decide(current(request).account, therapist_id, reason))
