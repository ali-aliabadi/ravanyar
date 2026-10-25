from collections.abc import Callable

import pytest
from django.db import DatabaseError, connection, transaction
from django.test import Client

from core.access import Grant, authorize, read_phone
from core.errors import AccessDeniedError
from core.models import AccessLog, Account, Decision, Purpose
from core.tests.conftest import bearer, make_phone

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def test_self_read_allowed_and_logged(sign_in: Callable[..., str]) -> None:
    phone = make_phone(20)
    response = Client().get("/api/me", **bearer(sign_in(phone)))
    assert response.status_code == 200
    account = Account.objects.get()
    assert response.json() == {"id": str(account.pk), "role": "client", "phone": phone}
    log = AccessLog.objects.get()
    assert (log.actor_id, log.subject_id, log.purpose, log.decision) == (
        account.pk,
        account.pk,
        Purpose.PROFILE,
        Decision.ALLOWED,
    )


def test_other_subject_denied_and_logged(sign_in: Callable[..., str]) -> None:
    sign_in(make_phone(21))
    sign_in(make_phone(22))
    actor, subject = Account.objects.all()
    with pytest.raises(AccessDeniedError):
        authorize(actor, subject, Purpose.PROFILE)
    log = AccessLog.objects.get()
    assert (log.actor_id, log.subject_id, log.decision) == (actor.pk, subject.pk, Decision.DENIED)


def test_grant_for_someone_else_decrypts_nothing(sign_in: Callable[..., str]) -> None:
    sign_in(make_phone(23))
    sign_in(make_phone(24))
    first, second = Account.objects.all()
    with pytest.raises(AccessDeniedError):
        read_phone(Grant(first.pk, first.pk, Purpose.PROFILE), second)


def test_access_log_rejects_update_and_delete(sign_in: Callable[..., str]) -> None:
    Client().get("/api/me", **bearer(sign_in(make_phone(25))))
    # The test runs in one transaction; TRUNCATE refuses while deferred FK checks are pending.
    connection.cursor().execute("SET CONSTRAINTS ALL IMMEDIATE")
    for sql in (
        "UPDATE core_accesslog SET decision = 'denied'",
        "DELETE FROM core_accesslog",
        "TRUNCATE core_accesslog",
    ):
        with pytest.raises(DatabaseError, match="append-only"), transaction.atomic():
            connection.cursor().execute(sql)
    assert AccessLog.objects.get().decision == Decision.ALLOWED
