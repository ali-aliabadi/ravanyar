"""SPEC-0003: therapist signup, credential upload, admin review and activation."""

from collections.abc import Callable
from io import StringIO
from typing import Any

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import CommandError, call_command
from django.test import Client
from django.test.utils import override_settings

from core.models import AccessLog, Account, Credential, Decision, Purpose, TherapistProfile
from core.tests.conftest import CURRENT, bearer, make_phone

pytestmark = [pytest.mark.integration, pytest.mark.django_db]
JSON = "application/json"
PDF = b"%PDF-1.4 invented licence scan"
PROFILE = {
    "display_name": "دکتر نمونه",
    "title": "روان‌شناس بالینی",
    "bio": "متن معرفی",
    "specialties": "اضطراب",
    "fee_rial": 9_000_000,
}


def upload(client: Client, token: str, data: bytes = PDF, kind: str = "license") -> Any:
    file = SimpleUploadedFile("scan.pdf", data, content_type="application/pdf")
    return client.post("/api/therapist/credentials", {"kind": kind, "file": file}, **bearer(token))


def ready_therapist(client: Client, sign_in: Callable[..., str], n: int) -> str:
    token = sign_in(make_phone(n), role="therapist")
    assert client.put("/api/therapist/profile", PROFILE, JSON, **bearer(token)).status_code == 200
    assert upload(client, token).status_code == 201
    return token


def admin(sign_in: Callable[..., str], n: int) -> str:
    token = sign_in(make_phone(n))
    call_command("grant_admin", make_phone(n), stdout=StringIO())
    return token


def test_profile_starts_as_draft(sign_in: Callable[..., str]) -> None:
    token = sign_in(make_phone(300), role="therapist")
    body = Client().get("/api/therapist/profile", **bearer(token)).json()
    assert (body["status"], body["credentials"]) == ("draft", [])


def test_client_cannot_use_therapist_or_admin_routes(sign_in: Callable[..., str]) -> None:
    client, token = Client(), sign_in(make_phone(301))
    assert client.get("/api/therapist/profile", **bearer(token)).status_code == 403
    assert client.get("/api/admin/therapists", **bearer(token)).status_code == 403


def test_upload_is_encrypted_and_type_comes_from_content(sign_in: Callable[..., str]) -> None:
    client = Client()
    token = sign_in(make_phone(302), role="therapist")
    body = upload(client, token).json()
    assert (body["mime"], body["size"]) == ("application/pdf", len(PDF))
    assert PDF not in bytes(Credential.objects.get().content_ct)
    assert upload(client, token, b"<script>not a pdf</script>").status_code == 422


def test_submit_needs_profile_and_licence(sign_in: Callable[..., str]) -> None:
    client = Client()
    token = sign_in(make_phone(303), role="therapist")
    assert client.post("/api/therapist/submit", **bearer(token)).status_code == 422
    client.put("/api/therapist/profile", PROFILE, JSON, **bearer(token))
    upload(client, token, kind="degree")
    assert client.post("/api/therapist/submit", **bearer(token)).status_code == 422
    upload(client, token)
    assert client.post("/api/therapist/submit", **bearer(token)).json()["status"] == "submitted"
    # Under review: nothing moves until an admin decides.
    assert client.put("/api/therapist/profile", PROFILE, JSON, **bearer(token)).status_code == 409
    assert upload(client, token).status_code == 409


def test_admin_reviews_reads_credential_and_approves(sign_in: Callable[..., str]) -> None:
    client = Client()
    therapist_token = ready_therapist(client, sign_in, 304)
    client.post("/api/therapist/submit", **bearer(therapist_token))
    admin_token = admin(sign_in, 305)

    queue = client.get("/api/admin/therapists", **bearer(admin_token)).json()
    assert len(queue) == 1
    credential_id = queue[0]["credentials"][0]["id"]
    file = client.get(f"/api/credentials/{credential_id}", **bearer(admin_token))
    assert (file.status_code, file.content, file["Content-Disposition"]) == (200, PDF, "attachment")
    log = AccessLog.objects.filter(purpose=Purpose.CREDENTIALS).get()
    assert log.decision == Decision.ALLOWED

    url = f"/api/admin/therapists/{queue[0]['id']}/decision"
    assert client.post(url, {"approve": True}, JSON, **bearer(admin_token)).status_code == 200
    assert TherapistProfile.objects.get().status == "approved"
    assert client.post(url, {"approve": True}, JSON, **bearer(admin_token)).status_code == 409

    # Changing what clients read sends the profile back for review; the fee does not.
    fee_only = PROFILE | {"fee_rial": 9_500_000}
    put = client.put("/api/therapist/profile", fee_only, JSON, **bearer(therapist_token))
    assert put.json()["status"] == "approved"
    renamed = PROFILE | {"display_name": "نام دیگر"}
    put = client.put("/api/therapist/profile", renamed, JSON, **bearer(therapist_token))
    assert put.json()["status"] == "submitted"


def test_reject_with_reason_lets_therapist_fix_and_resubmit(sign_in: Callable[..., str]) -> None:
    client = Client()
    therapist_token = ready_therapist(client, sign_in, 306)
    client.post("/api/therapist/submit", **bearer(therapist_token))
    admin_token = admin(sign_in, 307)
    profile_id = TherapistProfile.objects.get().pk
    body = {"approve": False, "reason": "unreadable"}
    url = f"/api/admin/therapists/{profile_id}/decision"
    client.post(url, body, JSON, **bearer(admin_token))
    mine = client.get("/api/therapist/profile", **bearer(therapist_token)).json()
    assert (mine["status"], mine["reject_reason"]) == ("rejected", "unreadable")
    assert upload(client, therapist_token).status_code == 201
    assert client.post("/api/therapist/submit", **bearer(therapist_token)).status_code == 200


def test_other_therapist_cannot_read_credential(sign_in: Callable[..., str]) -> None:
    client = Client()
    ready_therapist(client, sign_in, 308)
    other = sign_in(make_phone(309), role="therapist")
    credential = Credential.objects.get()
    assert client.get(f"/api/credentials/{credential.pk}", **bearer(other)).status_code == 403
    assert AccessLog.objects.get(purpose=Purpose.CREDENTIALS).decision == Decision.DENIED


def test_deleting_therapist_blanks_published_profile(sign_in: Callable[..., str]) -> None:
    client = Client()
    token = ready_therapist(client, sign_in, 310)
    client.delete("/api/me", **bearer(token))
    profile = TherapistProfile.objects.get()
    assert (profile.display_name, profile.bio, profile.status) == ("", "", "draft")


def test_admin_sign_in_only_for_staging_test_numbers(sent_codes: dict[str, str]) -> None:
    phone, client = make_phone(311), Client()
    with override_settings(TEST_PHONES=frozenset({phone}), TEST_CODE="424242"):
        client.post("/api/auth/code", {"phone": phone}, JSON)
        body = {"phone": phone, "code": "424242", "role": "admin", **CURRENT}
        assert client.post("/api/auth/verify", body, JSON).status_code == 200
    assert Account.objects.get().role == "admin"


def test_grant_admin_needs_an_existing_account() -> None:
    with pytest.raises(CommandError):
        call_command("grant_admin", make_phone(312), stdout=StringIO())


def test_seed_only_on_prelaunch_and_idempotent() -> None:
    call_command("seed_staging", stdout=StringIO())
    assert not TherapistProfile.objects.exists()
    with override_settings(PRELAUNCH=True):
        call_command("seed_staging", stdout=StringIO())
        call_command("seed_staging", stdout=StringIO())
    assert TherapistProfile.objects.filter(status="approved").count() == 4
