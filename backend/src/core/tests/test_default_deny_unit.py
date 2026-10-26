"""Default-deny: a route without auth must be on PUBLIC, or this fails (SPEC-0001)."""

import pytest
from django.test import Client

from config.urls import api

pytestmark = pytest.mark.unit

PUBLIC = {
    ("get", "/api/health"),
    ("get", "/api/ready"),
    ("post", "/api/auth/code"),
    ("post", "/api/auth/verify"),
}


def operations() -> list[tuple[str, str, dict[str, object]]]:
    paths = api.get_openapi_schema()["paths"]
    return [(method, path, op) for path, ops in paths.items() for method, op in ops.items()]


def test_every_route_requires_auth() -> None:
    open_routes = {(method, path) for method, path, op in operations() if not op.get("security")}
    assert open_routes == PUBLIC


def test_no_token_is_401_everywhere_but_public() -> None:
    client = Client()
    for method, path, _ in operations():
        if (method, path) in PUBLIC:
            continue
        url = path.replace("{document}", "terms")
        response = client.generic(method.upper(), url)
        assert response.status_code == 401, (method, path)
