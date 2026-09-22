"""Core HTTP surface. This module is the reference pattern: thin view, typed schema, no logic."""

from django.db import connection
from django.http import HttpRequest
from ninja import Router, Schema

router = Router()


class Health(Schema):
    status: str


@router.get("/health", response=Health)
def health(request: HttpRequest) -> Health:
    """Liveness: the process is up. Touches nothing, so it never flaps."""
    return Health(status="ok")


@router.get("/ready", response=Health)
def ready(request: HttpRequest) -> Health:
    """Readiness: the database answers. Fails the check when Postgres is unreachable."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return Health(status="ready")
