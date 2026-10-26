from collections.abc import Callable
from datetime import timedelta

import pytest
from django.test import Client
from django.utils import timezone

from core.models import Account, AuthSession, Consent, SignInCode
from core.tests.conftest import CURRENT, bearer, make_phone

pytestmark = [pytest.mark.integration, pytest.mark.django_db]
JSON = "application/json"


def request_code(client: Client, phone: str) -> int:
    return client.post("/api/auth/code", {"phone": phone}, JSON).status_code


def verify(client: Client, phone: str, code: str, role: str = "client") -> int:
    body = {"phone": phone, "code": code, "role": role, **CURRENT}
    return client.post("/api/auth/verify", body, JSON).status_code


def wrong(code: str) -> str:
    return f"{(int(code) + 1) % 10**6:06d}"


def test_request_same_response_with_or_without_account(
    sign_in: Callable[..., str], sent_codes: dict[str, str]
) -> None:
    client = Client()
    sign_in(make_phone(1))
    SignInCode.objects.all().delete()  # clear the resend limit for the existing account
    existing = client.post("/api/auth/code", {"phone": make_phone(1)}, JSON)
    unknown = client.post("/api/auth/code", {"phone": make_phone(2)}, JSON)
    assert (existing.status_code, existing.content) == (unknown.status_code, unknown.content)
    assert existing.status_code == 202
    assert set(sent_codes) == {make_phone(1), make_phone(2)}


def test_invalid_phone_is_422_without_echo() -> None:
    raw = "0" + "21" + "55501234"
    response = Client().post("/api/auth/code", {"phone": raw}, JSON)
    assert response.status_code == 422
    assert raw not in response.content.decode()


def test_rate_limited(sent_codes: dict[str, str]) -> None:
    client, phone = Client(), make_phone(3)
    assert request_code(client, phone) == 202
    assert request_code(client, phone) == 429  # within 60 seconds
    SignInCode.objects.update(created_at=timezone.now() - timedelta(minutes=2))
    for _ in range(4):
        assert request_code(client, phone) == 202
        SignInCode.objects.update(created_at=timezone.now() - timedelta(minutes=2))
    sent_codes.clear()
    assert request_code(client, phone) == 429  # 5 in the last hour
    assert sent_codes == {}


def test_wrong_code_five_times_kills_code(sent_codes: dict[str, str]) -> None:
    client, phone = Client(), make_phone(4)
    request_code(client, phone)
    code = sent_codes[phone]
    for _ in range(5):
        assert verify(client, phone, wrong(code)) == 400
    assert verify(client, phone, code) == 400
    assert not Account.objects.exists()


def test_expired_or_used_code_refused(sent_codes: dict[str, str]) -> None:
    client, phone = Client(), make_phone(5)
    request_code(client, phone)
    assert verify(client, phone, sent_codes[phone]) == 200
    assert verify(client, phone, sent_codes[phone]) == 400  # used

    SignInCode.objects.all().delete()
    request_code(client, phone)
    SignInCode.objects.update(expires_at=timezone.now())
    assert verify(client, phone, sent_codes[phone]) == 400  # expired


def test_persian_digits_in_code_accepted(sent_codes: dict[str, str]) -> None:
    client, phone = Client(), make_phone(6)
    request_code(client, phone)
    persian_digits = "".join(chr(0x06F0 + d) for d in range(10))
    persian = sent_codes[phone].translate(str.maketrans("0123456789", persian_digits))
    assert verify(client, phone, persian) == 200


def test_first_signin_creates_account_and_consents(sign_in: Callable[..., str]) -> None:
    sign_in(make_phone(7), role="therapist")
    account = Account.objects.get()
    assert account.role == "therapist"
    assert {(c.document, c.version) for c in Consent.objects.filter(account=account)} == {
        ("terms", CURRENT["terms_version"]),
        ("privacy", CURRENT["privacy_version"]),
    }
    SignInCode.objects.all().delete()  # clear the resend limit
    sign_in(make_phone(7), role="client", client=Client())  # existing account: role unchanged
    account.refresh_from_db()
    assert (Account.objects.count(), account.role) == (1, "therapist")


def test_admin_role_rejected(sent_codes: dict[str, str]) -> None:
    client, phone = Client(), make_phone(8)
    request_code(client, phone)
    assert verify(client, phone, sent_codes[phone], role="admin") == 422
    assert not Account.objects.exists()


def test_outdated_consent_version_rejected(sent_codes: dict[str, str]) -> None:
    client, phone = Client(), make_phone(9)
    request_code(client, phone)
    body = {"phone": phone, "code": sent_codes[phone], "role": "client", **CURRENT}
    body["terms_version"] = "terms-0"
    assert client.post("/api/auth/verify", body, JSON).status_code == 422


def test_no_or_bad_token_401() -> None:
    client = Client()
    assert client.get("/api/me").status_code == 401
    assert client.get("/api/me", **bearer("not-a-real-token")).status_code == 401


def test_logout_revokes(sign_in: Callable[..., str]) -> None:
    client, token = Client(), sign_in(make_phone(10))
    assert client.get("/api/me", **bearer(token)).status_code == 200
    assert client.post("/api/auth/logout", **bearer(token)).status_code == 204
    assert client.get("/api/me", **bearer(token)).status_code == 401


def test_expired_session_401(sign_in: Callable[..., str]) -> None:
    client, token = Client(), sign_in(make_phone(11))
    AuthSession.objects.update(expires_at=timezone.now())
    assert client.get("/api/me", **bearer(token)).status_code == 401


def test_session_lasts_thirty_days(sign_in: Callable[..., str]) -> None:
    sign_in(make_phone(12))
    session = AuthSession.objects.get()
    assert abs(session.expires_at - session.created_at - timedelta(days=30)) < timedelta(minutes=1)
