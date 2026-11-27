"""Client search for approved therapists (SPEC-0004). Services.

The search text says what a person is looking for help with: never log or store it.
"""

from uuid import UUID

from django.db.models import CharField, F, Func, QuerySet, Value
from django.db.models.functions import Concat, Replace

from core.errors import NotFoundError
from core.models import Review, Specialty, TherapistProfile

# Keyboards differ: Arabic yeh/kaf and the half-space (ZWNJ) must not decide a match.
VARIANTS = {"ي": "ی", "ك": "ک", "‌": ""}


def normalise(text: str) -> str:
    for old, new in VARIANTS.items():
        text = text.replace(old, new)
    return text.strip()


def _approved() -> QuerySet[TherapistProfile]:
    return TherapistProfile.objects.filter(
        status=Review.APPROVED, account__is_active=True
    ).order_by(F("reviewed_at").desc(nulls_last=True), "pk")


def search(q: str, specialty: Specialty | None = None) -> QuerySet[TherapistProfile]:
    """Approved profiles that chose `specialty` and whose name or title contains `q`, newest
    approval first. Either may be empty."""
    profiles = _approved()
    if specialty:
        profiles = profiles.filter(specialties__contains=[specialty])
    q = normalise(q)
    if not q:
        return profiles
    text: Func = Concat("display_name", Value(" "), "title", output_field=CharField())
    for old, new in VARIANTS.items():
        text = Replace(text, Value(old), Value(new))
    return profiles.annotate(text=text).filter(text__icontains=q)


def public_profile(therapist_id: UUID) -> TherapistProfile:
    """Not approved and not existing look the same: 404."""
    profile = _approved().filter(pk=therapist_id).first()
    if profile is None:
        raise NotFoundError
    return profile
