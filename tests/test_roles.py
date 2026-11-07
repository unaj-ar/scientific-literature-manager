from unittest.mock import MagicMock

import pytest

from fastapi import HTTPException

import api
from services.user_service import UserService


@pytest.fixture
def articles_service(monkeypatch):
    svc = MagicMock()
    svc.fetch_prioritized_list.return_value = []
    svc.register_new_article.return_value = 5
    monkeypatch.setattr(api, "service", svc)
    return svc


ARTICLE = {"title": "Paper", "authors": "A B"}


def test_articles_require_token(client, articles_service):
    assert client.get("/articles").status_code == 401
    assert client.post("/articles", json=ARTICLE).status_code == 401


def test_researcher_can_read_and_create_articles(client, add_user, auth, articles_service):
    add_user("rita")
    headers = auth("rita")
    assert client.get("/articles", headers=headers).status_code == 200
    assert client.post("/articles", json=ARTICLE, headers=headers).status_code == 200


def test_me_returns_role_and_permissions(client, add_user, auth):
    add_user("rita")
    add_user("root", "admin")
    assert "users:manage" not in client.get("/me", headers=auth("rita")).json()["permissions"]
    me = client.get("/me", headers=auth("root")).json()
    assert me["role"] == "admin" and "users:manage" in me["permissions"]


@pytest.mark.parametrize("method,path", [
    ("get", "/users"),
    ("delete", "/users/1"),
    ("patch", "/users/1/restore"),
    ("patch", "/users/1/role"),
])
def test_researcher_forbidden_on_user_management(client, add_user, auth, method, path):
    add_user("rita")
    kwargs = {"json": {"role": "admin"}} if path.endswith("/role") else {}
    assert getattr(client, method)(path, headers=auth("rita"), **kwargs).status_code == 403


def test_researcher_cannot_create_users(client, add_user, auth):
    add_user("rita")
    res = client.post("/users", headers=auth("rita"),
                      json={"username": "x1x", "email": "x@example.com", "password": "s3cretpass"})
    assert res.status_code == 403


def test_admin_lists_users_including_inactive(client, add_user, auth, repo):
    add_user("root", "admin")
    bob = add_user("bob")
    repo.users[bob]["is_active"] = False
    res = client.get("/users", headers=auth("root"))
    assert res.status_code == 200
    assert {u["username"] for u in res.json()} == {"root", "bob"}


def test_admin_creates_user_with_role(client, add_user, auth, repo):
    add_user("root", "admin")
    res = client.post("/users", headers=auth("root"), json={
        "username": "carol", "email": "carol@example.com", "password": "s3cretpass", "role": "admin"})
    assert res.status_code == 201
    assert repo.users[res.json()["id"]]["role"] == "admin"


def test_admin_rejects_invalid_role(client, add_user, auth):
    add_user("root", "admin")
    res = client.post("/users", headers=auth("root"), json={
        "username": "carol", "email": "carol@example.com", "password": "s3cretpass", "role": "superuser"})
    assert res.status_code == 422


def test_admin_changes_role_of_other_user(client, add_user, auth, repo):
    add_user("root", "admin")
    bob = add_user("bob")
    assert client.patch(f"/users/{bob}/role", json={"role": "admin"}, headers=auth("root")).status_code == 200
    assert repo.users[bob]["role"] == "admin"


def test_admin_cannot_change_own_role(client, add_user, auth):
    root = add_user("root", "admin")
    assert client.patch(f"/users/{root}/role", json={"role": "researcher"}, headers=auth("root")).status_code == 400


def test_service_blocks_demoting_or_deactivating_last_active_admin():
    """Salvaguarda del servicio: el actor ya no cuenta como admin (p. ej. cambió entre requests)."""
    repo = MagicMock()
    repo.get_by_id.return_value = {"id": 2, "role": "admin", "is_active": True}
    repo.count_active_admins.return_value = 1
    service = UserService(repo)

    with pytest.raises(HTTPException) as demote:
        service.change_role(2, "researcher", current_user_id=1)
    with pytest.raises(HTTPException) as deactivate:
        service.deactivate_user(2, current_user_id=1)

    assert demote.value.status_code == deactivate.value.status_code == 400
    repo.set_role.assert_not_called()
    repo.soft_delete.assert_not_called()


def test_admin_delete_and_restore_flow(client, add_user, auth):
    add_user("root", "admin")
    bob = add_user("bob")
    headers = auth("root")
    assert client.delete(f"/users/{bob}", headers=headers).status_code == 200
    assert client.delete("/users/999", headers=headers).status_code == 404
    assert client.patch(f"/users/{bob}/restore", headers=headers).status_code == 200
    assert client.patch(f"/users/{bob}/restore", headers=headers).status_code == 404


def test_deactivated_user_token_stops_working(client, add_user, auth, repo):
    add_user("root", "admin")
    rita = add_user("rita")
    headers = auth("rita")
    assert client.get("/me", headers=headers).status_code == 200
    client.delete(f"/users/{rita}", headers=auth("root"))
    assert client.get("/me", headers=headers).status_code == 401


def test_role_change_applies_to_existing_token(client, add_user, auth):
    add_user("root", "admin")
    rita = add_user("rita")
    rita_headers = auth("rita")
    assert client.get("/users", headers=rita_headers).status_code == 403
    client.patch(f"/users/{rita}/role", json={"role": "admin"}, headers=auth("root"))
    assert client.get("/users", headers=rita_headers).status_code == 200
