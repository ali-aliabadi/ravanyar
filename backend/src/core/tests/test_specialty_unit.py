"""SPEC-0004: migration 0004 turns old free-text specialties into codes."""

from importlib import import_module

import pytest

pytestmark = pytest.mark.unit
codes_from_text = import_module("core.migrations.0004_specialty_list").codes_from_text


@pytest.mark.parametrize(
    ("text", "codes"),
    [
        ("اضطراب، افسردگی، CBT", ["anxiety", "depression"]),
        ("اختلال خواب، اضطراب", ["anxiety", "sleep"]),
        ("زوج‌درمانی، روابط", ["couples"]),
        ("زوجدرمانی", ["couples"]),  # no half-space
        ("افسردگي", ["depression"]),  # Arabic yeh
        ("Anxiety, OCD", ["anxiety", "ocd"]),
        ("ذهن‌آگاهی", []),  # not on the list: dropped
    ],
)
def test_old_text_maps_to_codes(text: str, codes: list[str]) -> None:
    assert codes_from_text(text) == codes
