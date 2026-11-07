import pytest
from django.test import Client

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def test_ready_queries_a_real_postgres() -> None:
    response = Client().get("/api/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
