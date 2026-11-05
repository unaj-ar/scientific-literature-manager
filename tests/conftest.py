import pytest
from fastapi.testclient import TestClient

import api
from services.auth_service import AuthService

PASSWORD = "s3cretpass"


class FakeUserRepo:
    """Repositorio en memoria para probar la API sin PostgreSQL."""

    def __init__(self):
        self.users = {}
        self.next_id = 1

    def exists(self, username, email):
        return any(u["username"] == username or u["email"] == email for u in self.users.values())

    def create(self, username, email, hashed_password, role="researcher"):
        uid = self.next_id
        self.next_id += 1
        self.users[uid] = {"id": uid, "username": username, "email": email,
                           "hashed_password": hashed_password, "is_active": True, "role": role}
        return uid

    def get_by_username(self, username):
        return next((u for u in self.users.values() if u["username"] == username), None)

    def get_by_id(self, user_id):
        return self.users.get(user_id)

    def list_all(self):
        return list(self.users.values())

    def set_role(self, user_id, role):
        self.users[user_id]["role"] = role
        return True

    def count_active_admins(self):
        return sum(1 for u in self.users.values() if u["role"] == "admin" and u["is_active"])

    def soft_delete(self, user_id):
        user = self.users.get(user_id)
        if not user or not user["is_active"]:
            return False
        user["is_active"] = False
        return True

    def restore(self, user_id):
        user = self.users.get(user_id)
        if not user or user["is_active"]:
            return False
        user["is_active"] = True
        return True


@pytest.fixture
def repo():
    return FakeUserRepo()


@pytest.fixture
def client(repo):
    api.app.dependency_overrides[api.get_user_repository] = lambda: repo
    yield TestClient(api.app)
    api.app.dependency_overrides.clear()


@pytest.fixture
def add_user(repo):
    """Crea un usuario directo en el repo y retorna su id."""
    def _add(username, role="researcher"):
        return repo.create(username, f"{username}@example.com", AuthService.hash_password(PASSWORD), role)
    return _add


@pytest.fixture
def auth(client):
    """Hace login y retorna el header Authorization."""
    def _auth(username):
        res = client.post("/login", data={"username": username, "password": PASSWORD})
        return {"Authorization": f"Bearer {res.json()['access_token']}"}
    return _auth
