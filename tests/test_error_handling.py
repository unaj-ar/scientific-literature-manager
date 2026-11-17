import psycopg2
import pytest
from fastapi.testclient import TestClient
from psycopg2 import errors as pg_errors
from unittest.mock import MagicMock

import api

ARTICLE = {"title": "Paper", "authors": "A B"}


@pytest.fixture
def failing_service(monkeypatch):
    svc = MagicMock()
    monkeypatch.setattr(api, "service", svc)
    return svc


@pytest.fixture
def lenient_client(client):
    # Let the app answer 500 instead of re-raising the exception into the test.
    return TestClient(api.app, raise_server_exceptions=False)


def _login(client, add_user, auth):
    add_user("rita")
    return auth("rita")


def test_unhandled_error_hides_internal_text(lenient_client, client, add_user, auth, failing_service):
    headers = _login(client, add_user, auth)
    failing_service.register_new_article.side_effect = RuntimeError("password=hunter2 in dsn")

    response = lenient_client.post("/articles", json=ARTICLE, headers=headers)

    assert response.status_code == 500
    assert response.json()["detail"] == "Error interno del servidor."
    assert "hunter2" not in response.text


def test_duplicate_key_returns_409(lenient_client, client, add_user, auth, failing_service):
    headers = _login(client, add_user, auth)
    failing_service.register_new_article.side_effect = pg_errors.UniqueViolation("dup key")

    response = lenient_client.post("/articles", json=ARTICLE, headers=headers)

    assert response.status_code == 409


def test_database_down_returns_503(lenient_client, client, add_user, auth, failing_service):
    headers = _login(client, add_user, auth)
    failing_service.register_new_article.side_effect = psycopg2.OperationalError("connection refused")

    response = lenient_client.post("/articles", json=ARTICLE, headers=headers)

    assert response.status_code == 503
    assert "connection refused" not in response.text


def test_request_id_header_is_echoed(client):
    response = client.get("/login.html", headers={"X-Request-ID": "abc123"})

    assert response.headers["X-Request-ID"] == "abc123"
