"""SPEC-0004: free-text specialties become codes from a fixed list.

Text that clearly names a specialty becomes its code; the rest is dropped. Written directly,
not through `update_profile`, so approved profiles stay approved.
"""

from typing import Any

import django.contrib.postgres.fields
from django.db import migrations, models

# Frozen here: a migration must not change when the app's list does.
LABELS = {
    "anxiety": "اضطراب",
    "depression": "افسردگی",
    "couples": "زوج‌درمانی",
    "family": "خانواده‌درمانی",
    "child": "کودک",
    "adolescent": "نوجوان",
    "trauma": "تروما",
    "addiction": "اعتیاد",
    "sleep": "خواب",
    "ocd": "وسواس",
    "grief": "سوگ",
    "work_stress": "استرس شغلی",
}
VARIANTS = {"ي": "ی", "ك": "ک", "‌": ""}


def _plain(text: str) -> str:
    for old, new in VARIANTS.items():
        text = text.replace(old, new)
    return text.lower()


def codes_from_text(text: str) -> list[str]:
    plain = _plain(text)
    return [c for c, label in LABELS.items() if _plain(label) in plain or c in plain][:5]


def forward(apps: Any, schema_editor: Any) -> None:
    profiles = apps.get_model("core", "TherapistProfile")
    for profile in profiles.objects.exclude(specialties=""):
        profile.specialty_codes = codes_from_text(profile.specialties)
        profile.save(update_fields=["specialty_codes"])


def backward(apps: Any, schema_editor: Any) -> None:
    profiles = apps.get_model("core", "TherapistProfile")
    for profile in profiles.objects.exclude(specialty_codes=[]):
        profile.specialties = "، ".join(LABELS[c] for c in profile.specialty_codes)
        profile.save(update_fields=["specialties"])


class Migration(migrations.Migration):
    dependencies = [("core", "0003_therapist_verification")]

    operations = [
        migrations.AddField(
            model_name="therapistprofile",
            name="specialty_codes",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(
                    choices=[
                        ("anxiety", "Anxiety"),
                        ("depression", "Depression"),
                        ("couples", "Couples"),
                        ("family", "Family"),
                        ("child", "Child"),
                        ("adolescent", "Adolescent"),
                        ("trauma", "Trauma"),
                        ("addiction", "Addiction"),
                        ("sleep", "Sleep"),
                        ("ocd", "Ocd"),
                        ("grief", "Grief"),
                        ("work_stress", "Work Stress"),
                    ],
                    max_length=32,
                ),
                blank=True,
                default=list,
                size=5,
            ),
        ),
        migrations.RunPython(forward, backward),
        migrations.RemoveField(model_name="therapistprofile", name="specialties"),
        migrations.RenameField(
            model_name="therapistprofile", old_name="specialty_codes", new_name="specialties"
        ),
    ]
