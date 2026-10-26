from collections.abc import Callable

import pytest
from cryptography.exceptions import InvalidTag
from django.test import Client

from core.crypto import aad, decrypt, new_data_key
from core.models import Account, AuthSession, SignInCode
from core.tests.conftest import bearer, make_phone

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def test_delete_shreds(sign_in: Callable[..., str]) -> None:
    client, token = Client(), sign_in(make_phone(40))
    stolen = Account.objects.get()  # a copy taken before deletion, as a backup would be
    stolen_ct = bytes(stolen.phone_ct or b"")

    assert client.delete("/api/me", **bearer(token)).status_code == 204

    account = Account.objects.get()
    assert (account.wrapped_key, account.phone_ct, account.phone_index) == (None, None, None)
    assert not account.is_active and account.deleted_at is not None
    assert not AuthSession.objects.filter(revoked_at=None).exists()
    assert not SignInCode.objects.exists()
    assert client.get("/api/me", **bearer(token)).status_code == 401
    # Without the wrapped key nothing opens the old ciphertext; a fresh key does not either.
    with pytest.raises(InvalidTag):
        decrypt(new_data_key(), aad("core_account", "phone", account.pk), stolen_ct)


def test_resignup_creates_new_account(sign_in: Callable[..., str]) -> None:
    client = Client()
    client.delete("/api/me", **bearer(sign_in(make_phone(41))))
    SignInCode.objects.all().delete()
    sign_in(make_phone(41))
    old, new = Account.objects.order_by("created_at")
    assert old.pk != new.pk
    assert old.deleted_at is not None and new.is_active
