import pytest
from django.test import Client

pytestmark = pytest.mark.unit


def test_health_is_ok_without_a_database() -> None:
    response = Client().get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
