"""ADR 0004's leak test: dump every value in the database and look for a phone number."""

from collections.abc import Callable

import pytest
from django.db import connection
from django.test import Client

from core.tests.conftest import bearer, make_phone

pytestmark = [pytest.mark.integration, pytest.mark.django_db]
TYPES = ("text", "character varying", "jsonb", "bytea")


def every_value() -> list[str | bytes]:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT table_name, column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND data_type = ANY(%s)",
            [list(TYPES)],
        )
        columns = cursor.fetchall()
        values: list[str | bytes] = []
        for table, column in columns:
            cursor.execute(f'SELECT "{column}" FROM "{table}"')  # noqa: S608 - names from catalog
            values += [bytes(v) if isinstance(v, memoryview) else v for (v,) in cursor if v]
    return values


def test_no_phone_in_any_column(sign_in: Callable[..., str]) -> None:
    phones = [make_phone(50), make_phone(51)]
    client = Client()
    for phone in phones:
        token = sign_in(phone)
        client.get("/api/me", **bearer(token))
    client.delete("/api/me", **bearer(token))

    values = every_value()
    assert values, "the scan found nothing to scan"
    for phone in phones:
        national = phone[3:].encode()  # every written form contains these ten digits
        for value in values:
            assert national not in (value if isinstance(value, bytes) else value.encode())
