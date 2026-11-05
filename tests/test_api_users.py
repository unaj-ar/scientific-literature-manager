def register(client, username="alice", email="alice@example.com", password="s3cretpass"):
    return client.post("/register", json={"username": username, "email": email, "password": password})


def test_register_stores_hash_not_password(client, repo):
    res = register(client)
    assert res.status_code == 201
    stored = repo.users[res.json()["id"]]["hashed_password"]
    assert stored != "s3cretpass"


def test_register_always_creates_researcher_even_if_role_sent(client, repo):
    res = client.post("/register", json={"username": "eve", "email": "eve@example.com",
                                         "password": "s3cretpass", "role": "admin"})
    assert res.status_code == 201
    assert repo.users[res.json()["id"]]["role"] == "researcher"


def test_register_duplicate_returns_409(client):
    register(client)
    assert register(client).status_code == 409


def test_register_short_password_returns_422(client):
    assert register(client, password="short").status_code == 422


def test_login_ok_returns_token_and_role(client):
    register(client)
    res = client.post("/login", data={"username": "alice", "password": "s3cretpass"})
    assert res.status_code == 200
    assert res.json()["token_type"] == "bearer"
    assert res.json()["role"] == "researcher"


def test_login_wrong_password_and_unknown_user_same_error(client):
    register(client)
    bad_pass = client.post("/login", data={"username": "alice", "password": "wrongpass"})
    unknown = client.post("/login", data={"username": "nobody", "password": "wrongpass"})
    assert bad_pass.status_code == unknown.status_code == 401
    assert bad_pass.json() == unknown.json()


def test_login_inactive_user_rejected(client, repo):
    uid = register(client).json()["id"]
    repo.users[uid]["is_active"] = False
    assert client.post("/login", data={"username": "alice", "password": "s3cretpass"}).status_code == 401
