"""Client search for approved therapists (SPEC-0004). Thin views, as in `api.py`."""

from uuid import UUID

from django.db.models import QuerySet
from django.http import HttpRequest
from ninja import Router, Schema
from ninja.pagination import PageNumberPagination, paginate
from pydantic import Field

from core import search
from core.models import Specialty, TherapistProfile

router = Router()


class SearchIn(Schema):
    # In the body, never the URL: a query string lands in every access log on the way.
    q: str = Field(default="", max_length=100)
    specialty: Specialty | None = None


class PublicProfileOut(Schema):
    """Only what the therapist published. Never status, review or credential fields."""

    id: UUID
    display_name: str
    title: str
    specialties: list[Specialty]
    bio: str
    fee_rial: int | None

    @staticmethod
    def resolve_id(profile: TherapistProfile) -> UUID:
        return profile.account_id


@router.post("/therapists/search", response=list[PublicProfileOut])
@paginate(PageNumberPagination, page_size=20)
def search_therapists(request: HttpRequest, payload: SearchIn) -> QuerySet[TherapistProfile]:
    return search.search(payload.q, payload.specialty)


@router.get("/therapists/{therapist_id}", response=PublicProfileOut)
def public_profile(request: HttpRequest, therapist_id: UUID) -> PublicProfileOut:
    return PublicProfileOut.model_validate(search.public_profile(therapist_id))
