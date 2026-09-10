from datetime import datetime, timezone

import jwt
from app.config import settings
from app.models.user import Role, User
from app.services.auth import create_access_token, hash_password, verify_password


def test_password_hash_is_argon2id_and_verifies() -> None:
    password_hash = hash_password("correct horse battery staple")

    assert password_hash.startswith("$argon2id$")
    assert verify_password("correct horse battery staple", password_hash)
    assert not verify_password("wrong", password_hash)
    assert not verify_password("anything", "not-a-password-hash")


def test_access_token_contains_identity_role_and_one_hour_expiry() -> None:
    user = User(id=42, username="alice", role=Role.ADMIN, password_hash="hidden")
    before = datetime.now(timezone.utc).timestamp()
    token = create_access_token(user)
    claims = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])

    assert claims["sub"] == "42"
    assert claims["username"] == "alice"
    assert claims["role"] == "ADMIN"
    assert before + 3590 <= claims["exp"] <= before + 3610
