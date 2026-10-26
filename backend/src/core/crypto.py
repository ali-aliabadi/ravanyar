"""ADR 0004: per-person envelope encryption, the blind index, and phone normalisation.

Pure functions, no ORM. Keys come from settings, which load them from the environment.
"""

import base64
import binascii
import hashlib
import hmac
import os
import re
from uuid import UUID

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

NONCE_BYTES = 12
# Persian (U+06F0..) and Arabic-Indic (U+0660..) digits to 0-9.
_DIGITS = {zero + d: str(d) for zero in (0x06F0, 0x0660) for d in range(10)}
_MOBILE = re.compile(r"(?:\+98|0098|98|0)?(9[0-9]{9})")


def load_key(name: str, raw: str) -> bytes:
    """Decode a base64 key from the environment. Called by settings, so a bad key stops startup."""
    try:
        key = base64.b64decode(raw, validate=True)
    except binascii.Error:
        key = b""
    if len(key) != 32:
        raise ImproperlyConfigured(f"{name} must be 32 bytes, base64-encoded")
    return key


def aad(table: str, column: str, row_id: UUID) -> bytes:
    """Bind a ciphertext to its location, so it cannot be copied into another row."""
    return f"{table}|{column}|{row_id}".encode()


def encrypt(key: bytes, associated: bytes, plaintext: bytes) -> bytes:
    nonce = os.urandom(NONCE_BYTES)
    return nonce + AESGCM(key).encrypt(nonce, plaintext, associated)


def decrypt(key: bytes, associated: bytes, blob: bytes) -> bytes:
    """Raises cryptography.exceptions.InvalidTag on a wrong key, wrong location, or tampering."""
    return AESGCM(key).decrypt(blob[:NONCE_BYTES], blob[NONCE_BYTES:], associated)


def new_data_key() -> bytes:
    return AESGCM.generate_key(bit_length=256)


def wrap(account_id: UUID, data_key: bytes) -> bytes:
    return encrypt(settings.MASTER_KEY, str(account_id).encode(), data_key)


def unwrap(account_id: UUID, wrapped: bytes) -> bytes:
    return decrypt(settings.MASTER_KEY, str(account_id).encode(), wrapped)


def blind_index(value: str) -> str:
    return hmac.new(settings.BLIND_INDEX_KEY, value.encode(), hashlib.sha256).hexdigest()


def latin_digits(raw: str) -> str:
    """Persian and Arabic-Indic digits to 0-9: a Persian keyboard types the former."""
    return raw.translate(_DIGITS)


def normalise_phone(raw: str) -> str:
    """Any common form of an Iranian mobile number to +989XXXXXXXXX; anything else is refused."""
    digits = re.sub(r"[\s\-()]", "", latin_digits(raw))
    match = _MOBILE.fullmatch(digits)
    if match is None:
        raise ValueError("not an Iranian mobile number")
    return "+98" + match.group(1)
