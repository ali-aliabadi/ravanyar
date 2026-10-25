from uuid import uuid4

import pytest
from cryptography.exceptions import InvalidTag
from django.test import override_settings

from core.crypto import (
    aad,
    blind_index,
    decrypt,
    encrypt,
    new_data_key,
    normalise_phone,
    unwrap,
    wrap,
)
from core.tests.conftest import make_phone

pytestmark = pytest.mark.unit
LATIN = "0123456789"
PERSIAN = "".join(chr(0x06F0 + d) for d in range(10))  # escaped: ruff RUF001 flags the glyphs
ARABIC = "".join(chr(0x0660 + d) for d in range(10))


def test_round_trip() -> None:
    row = uuid4()
    data_key = unwrap(row, wrap(row, new_data_key()))
    blob = encrypt(data_key, aad("t", "c", row), b"secret")
    assert b"secret" not in blob
    assert decrypt(data_key, aad("t", "c", row), blob) == b"secret"


def test_aad_mismatch_fails() -> None:
    key, row_a, row_b = new_data_key(), uuid4(), uuid4()
    blob = encrypt(key, aad("t", "c", row_a), b"secret")
    with pytest.raises(InvalidTag):
        decrypt(key, aad("t", "c", row_b), blob)
    with pytest.raises(InvalidTag):
        unwrap(row_b, wrap(row_a, key))


def test_other_persons_key_fails() -> None:
    row = uuid4()
    blob = encrypt(new_data_key(), aad("t", "c", row), b"secret")
    with pytest.raises(InvalidTag):
        decrypt(new_data_key(), aad("t", "c", row), blob)


def test_blind_index_is_keyed() -> None:
    phone = make_phone(1)
    first = blind_index(phone)
    assert first == blind_index(phone)
    with override_settings(BLIND_INDEX_KEY=bytes(32)):
        assert blind_index(phone) != first


def test_phone_forms_normalise() -> None:
    expected = make_phone(1234567)
    national = expected[3:]  # 9XXXXXXXXX
    persian, arabic = (str.maketrans(LATIN, digits) for digits in (PERSIAN, ARABIC))
    forms = ["0" + national, "+98" + national, "98" + national, "0098" + national]
    forms += [("0" + national).translate(persian), ("+98" + national).translate(persian)]
    forms += [("0" + national).translate(arabic), "0" + national[:3] + " " + national[3:]]
    assert {normalise_phone(form) for form in forms} == {expected}


@pytest.mark.parametrize("raw", ["0" + "21" + "12345678", "+1" + "2025550100", "0" + "912123", ""])
def test_non_iranian_or_landline_rejected(raw: str) -> None:
    with pytest.raises(ValueError, match="not an Iranian mobile number"):
        normalise_phone(raw)
