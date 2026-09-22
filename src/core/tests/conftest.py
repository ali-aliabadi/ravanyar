"""Integration tests get a real Postgres from testcontainers; unit tests never start one."""

from collections.abc import Iterator

import pytest
from django.conf import settings
from django.test.utils import setup_databases
from testcontainers.community.postgres import PostgresContainer


@pytest.fixture(scope="session")
def django_db_setup(django_db_blocker: pytest.FixtureRequest) -> Iterator[None]:
    """Replace pytest-django's database with a throwaway container, migrations and all."""
    with PostgresContainer("postgres:17") as postgres:
        settings.DATABASES["default"] |= {
            "HOST": postgres.get_container_host_ip(),
            "PORT": str(postgres.get_exposed_port(5432)),
            "NAME": postgres.dbname,
            "USER": postgres.username,
            "PASSWORD": postgres.password,
        }
        with django_db_blocker.unblock():  # type: ignore[attr-defined]
            setup_databases(verbosity=0, interactive=False)
        yield
