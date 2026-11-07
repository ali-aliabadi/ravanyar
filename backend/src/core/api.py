"""Core HTTP surface. This module is the reference pattern: thin view, typed schema, no logic.

Every route needs `consented` auth (the NinjaAPI default) unless it names another, and
`test_default_deny_unit` fails when a new public route is not on its list.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from django.db import connection
from django.http import HttpRequest
from ninja import Router, Schema, Status
from pydantic import field_validator

from core import services
from core.auth import bearer, current
from core.crypto import latin_digits, normalise_phone
from core.models import Document, Role

router = Router()


class Health(Schema):
    status: str


class PhoneIn(Schema):
    phone: str

    @field_validator("phone")
    @classmethod
    def _phone(cls, value: str) -> str:
        return normalise_phone(value)


class VerifyIn(PhoneIn):
    code: str
    role: Literal[Role.CLIENT, Role.THERAPIST]
    terms_version: str
    privacy_version: str

    @field_validator("code")
    @classmethod
    def _code(cls, value: str) -> str:
        value = latin_digits(value)
        if len(value) != 6 or not value.isascii() or not value.isdigit():
            raise ValueError("code is 6 digits")
        return value


class TokenOut(Schema):
    token: str


class MeOut(Schema):
    id: UUID
    role: str
    phone: str


class ConsentIn(Schema):
    document: Document
    version: str


class ConsentOut(Schema):
    document: str
    version: str
    given_at: datetime
    withdrawn_at: datetime | None


@router.get("/health", response=Health, auth=None)
def health(request: HttpRequest) -> Health:
    """Liveness: the process is up. Touches nothing, so it never flaps."""
    return Health(status="ok")


@router.get("/ready", response=Health, auth=None)
def ready(request: HttpRequest) -> Health:
    """Readiness: the database answers. Fails the check when Postgres is unreachable."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return Health(status="ready")


@router.post("/auth/code", response={202: Health}, auth=None)
def request_code(request: HttpRequest, payload: PhoneIn) -> Status[Health]:
    services.request_code(payload.phone)
    return Status(202, Health(status="sent"))


@router.post("/auth/verify", response=TokenOut, auth=None)
def verify_code(request: HttpRequest, payload: VerifyIn) -> TokenOut:
    token = services.verify_code(
        payload.phone, payload.code, payload.role, payload.terms_version, payload.privacy_version
    )
    return TokenOut(token=token)


@router.post("/auth/logout", response={204: None}, auth=bearer)
def logout(request: HttpRequest) -> Status[None]:
    services.logout(current(request))
    return Status(204, None)


@router.get("/me", response=MeOut)
def me(request: HttpRequest) -> MeOut:
    account = current(request).account
    return MeOut(id=account.pk, role=account.role, phone=services.profile_phone(account))


@router.delete("/me", response={204: None}, auth=bearer)
def delete_me(request: HttpRequest) -> Status[None]:
    services.delete_account(current(request).account)
    return Status(204, None)


@router.get("/me/consents", response=list[ConsentOut], auth=bearer)
def list_consents(request: HttpRequest) -> list[ConsentOut]:
    consents = services.list_consents(current(request).account)
    return [ConsentOut.model_validate(c, from_attributes=True) for c in consents]


@router.post("/me/consents", response={201: None}, auth=bearer)
def grant_consent(request: HttpRequest, payload: ConsentIn) -> Status[None]:
    services.grant_consent(current(request).account, payload.document, payload.version)
    return Status(201, None)


@router.post("/me/consents/{document}/withdraw", response={204: None}, auth=bearer)
def withdraw_consent(request: HttpRequest, document: Document) -> Status[None]:
    services.withdraw_consent(current(request).account, document)
    return Status(204, None)
