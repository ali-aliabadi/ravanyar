"""Invented staging data, run by `manage.py seed_staging` on pre-launch deployments only.

Ids are derived from fixed names, so running it again updates the same rows. Each feature
spec adds its own demo data here.
"""

from uuid import NAMESPACE_URL, UUID, uuid5

from django.db import transaction
from django.utils import timezone

from core.crypto import new_data_key, wrap
from core.models import Account, Review, Role, TherapistProfile

# Invented people. Fees in rial.
THERAPISTS = [
    ("دکتر سارا نمونه", "روان‌شناس بالینی", "اضطراب، افسردگی، CBT", 12_000_000),
    ("دکتر امید آزمایشی", "روان‌شناس مشاوره", "زوج‌درمانی، روابط", 10_000_000),
    ("مریم فرضی", "کارشناس ارشد روان‌شناسی بالینی", "استرس شغلی، ذهن‌آگاهی", 8_000_000),
    ("دکتر رضا ساختگی", "روان‌پزشک", "اختلال خواب، اضطراب", 15_000_000),
]
BIO = "این پروفایل ساختگی و فقط برای نسخهٔ آزمایشی است."


def demo_id(name: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"ravanyar-demo:{name}")


def _account(pk: UUID, role: Role) -> Account:
    account = Account.objects.filter(pk=pk).first()
    if account is None:
        account = Account(pk=pk, role=role)
        account.wrapped_key = wrap(pk, new_data_key())
        account.set_unusable_password()
        account.save()
    return account


@transaction.atomic
def run() -> None:
    for name, title, specialties, fee in THERAPISTS:
        account = _account(demo_id(name), Role.THERAPIST)
        TherapistProfile.objects.update_or_create(
            account=account,
            defaults={
                "display_name": name,
                "title": title,
                "bio": BIO,
                "specialties": specialties,
                "fee_rial": fee,
                "status": Review.APPROVED,
                "reviewed_at": timezone.now(),
            },
        )
