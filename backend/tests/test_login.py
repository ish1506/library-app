import logging

from app.database import get_db
from app.models.enums import Role
from app.models.user import User
from app.services.auth import hash_password
from fastapi.testclient import TestClient
from main import app


class FakeSession:
    def __init__(self, user: User | None) -> None:
        self.user = user

    async def scalar(self, _query: object) -> User | None:
        return self.user


def client_for(user: User | None) -> TestClient:
    app.dependency_overrides[get_db] = lambda: FakeSession(user)
    return TestClient(app)


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_user_and_admin_can_login() -> None:
    for role in (Role.USER, Role.ADMIN):
        client = client_for(
            User(
                id=1, username="alice", password_hash=hash_password("secret"), role=role
            )
        )
        response = client.post(
            "/auth/login", json={"username": "alice", "password": "secret"}
        )
        assert response.status_code == 200
        assert response.json()["token_type"] == "bearer"
        assert response.json()["access_token"]


def test_unknown_and_wrong_password_have_identical_401_responses() -> None:
    valid = User(
        id=1, username="alice", password_hash=hash_password("secret"), role=Role.USER
    )
    unknown = client_for(None).post(
        "/auth/login", json={"username": "alice", "password": "secret"}
    )
    wrong = client_for(valid).post(
        "/auth/login", json={"username": "alice", "password": "wrong"}
    )

    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json() == {"detail": "Invalid username or password"}
    assert (
        unknown.headers["www-authenticate"]
        == wrong.headers["www-authenticate"]
        == "Bearer"
    )


def test_login_logs_request_without_credentials(caplog) -> None:
    caplog.set_level(logging.DEBUG, logger="uvicorn.error.library_api")
    client = client_for(
        User(
            id=1,
            username="alice",
            password_hash=hash_password("secret"),
            role=Role.USER,
        )
    )

    response = client.post(
        "/auth/login", json={"username": "alice", "password": "secret"}
    )

    assert response.headers["x-request-id"]
    assert "request_started" in caplog.text
    assert "request_completed" in caplog.text
    assert "secret" not in caplog.text


def test_malformed_login_body_is_rejected() -> None:
    response = client_for(None).post("/auth/login", json={"username": "alice"})

    assert response.status_code == 422
