import asyncio
from collections.abc import Generator
from dataclasses import dataclass
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Engine, create_engine, delete, insert, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from app.database import get_db
from app.models.book import Book
from app.models.book_loan import BookLoan
from app.models.enums import LoanStatus, Role
from app.models.user import User
from app.services.auth import create_access_token
from main import app


class AuthSession:
    def __init__(self, *users: User) -> None:
        self.users = {user.id: user for user in users}

    async def get(self, model: object, item_id: int) -> User | None:
        return self.users.get(item_id)


@dataclass
class LoanFixture:
    engine: Engine
    async_engine: AsyncEngine
    book_id: int
    user: User
    other_user: User
    admin: User


@pytest.fixture
def loan_fixture(database_url: str) -> Generator[LoanFixture, None, None]:
    engine = create_engine(database_url)
    async_engine = create_async_engine(database_url)
    username_suffix = uuid4().hex[:10]
    user = User(
        username=f"alice-{username_suffix}", password_hash="hash", role=Role.USER
    )
    other_user = User(
        username=f"bob-{username_suffix}", password_hash="hash", role=Role.USER
    )
    admin = User(
        username=f"admin-{username_suffix}", password_hash="hash", role=Role.ADMIN
    )
    isbn = f"978{uuid4().int % 10_000_000_000:010d}"
    try:
        with engine.begin() as connection:
            user.id = connection.execute(
                insert(User)
                .values(
                    username=user.username,
                    password_hash=user.password_hash,
                    role=user.role,
                )
                .returning(User.id)
            ).scalar_one()
            other_user.id = connection.execute(
                insert(User)
                .values(
                    username=other_user.username,
                    password_hash=other_user.password_hash,
                    role=other_user.role,
                )
                .returning(User.id)
            ).scalar_one()
            admin.id = connection.execute(
                insert(User)
                .values(
                    username=admin.username,
                    password_hash=admin.password_hash,
                    role=admin.role,
                )
                .returning(User.id)
            ).scalar_one()
            book_id = connection.execute(
                insert(Book)
                .values(
                    title="A Loan Test Book",
                    author="A Test Author",
                    date=1_700_000_000,
                    isbn=isbn,
                    loan_duration_days=14,
                    total_copies=1,
                    available_copies=1,
                    late_fee_cents_per_day=50,
                )
                .returning(Book.id)
            ).scalar_one()
    except OperationalError as error:
        async_engine.sync_engine.dispose()
        engine.dispose()
        pytest.skip(f"PostgreSQL test database is unavailable: {error}")

    async_session = async_sessionmaker(async_engine, expire_on_commit=False)

    async def override_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    fixture = LoanFixture(
        async_engine=async_engine,
        engine=engine,
        book_id=book_id,
        user=user,
        other_user=other_user,
        admin=admin,
    )
    try:
        yield fixture
    finally:
        app.dependency_overrides.clear()
        with engine.begin() as connection:
            connection.execute(delete(BookLoan).where(BookLoan.book_id == book_id))
            connection.execute(delete(Book).where(Book.id == book_id))
            connection.execute(
                delete(User).where(User.id.in_([user.id, other_user.id, admin.id]))
            )
        asyncio.run(async_engine.dispose())
        engine.dispose()


def setup_function() -> None:
    app.dependency_overrides.clear()


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_loan_routes_require_authentication_and_roles() -> None:
    user = User(id=1, username="alice", password_hash="hash", role=Role.USER)
    admin = User(id=2, username="admin", password_hash="hash", role=Role.ADMIN)
    app.dependency_overrides[get_db] = lambda: AuthSession(user, admin)
    client = TestClient(app)

    assert client.get("/loans/me").status_code == 401
    assert client.post("/books/1/loans").status_code == 401
    assert client.post("/loans/1/return").status_code == 401
    assert client.get("/books/1/loans").status_code == 401

    admin_headers = {"Authorization": f"Bearer {create_access_token(admin)}"}
    user_headers = {"Authorization": f"Bearer {create_access_token(user)}"}
    assert client.get("/loans/me", headers=admin_headers).status_code == 403
    assert client.post("/books/1/loans", headers=admin_headers).status_code == 403
    assert client.post("/loans/1/return", headers=admin_headers).status_code == 403
    assert client.get("/books/1/loans", headers=user_headers).status_code == 403


def test_loan_lifecycle_inventory_and_history(loan_fixture: LoanFixture) -> None:
    fixture = loan_fixture
    user_headers = {"Authorization": f"Bearer {create_access_token(fixture.user)}"}
    other_headers = {
        "Authorization": f"Bearer {create_access_token(fixture.other_user)}"
    }
    admin_headers = {"Authorization": f"Bearer {create_access_token(fixture.admin)}"}
    client = TestClient(app)

    borrowed = client.post(f"/books/{fixture.book_id}/loans", headers=user_headers)
    assert borrowed.status_code == 201
    loan = borrowed.json()
    assert loan["status"] == LoanStatus.BORROWED
    assert loan["late_fee_cents"] == 0
    assert loan["due_at_timestamp"] - loan["loan_timestamp"] == 14 * 86_400

    assert client.post(
        f"/books/{fixture.book_id}/loans", headers=user_headers
    ).json() == {"detail": "Book is unavailable"}
    assert client.patch(
        f"/books/{fixture.book_id}",
        json={"total_copies": 0},
        headers=admin_headers,
    ).json() == {"detail": "total_copies cannot be reduced below checked-out copies"}
    assert client.get("/loans/me", headers=user_headers).json() == [loan]
    assert client.get(
        f"/books/{fixture.book_id}/loans", headers=admin_headers
    ).json() == [loan]
    assert (
        client.post(f"/loans/{loan['id']}/return", headers=other_headers).status_code
        == 403
    )

    returned = client.post(f"/loans/{loan['id']}/return", headers=user_headers)
    assert returned.status_code == 200
    assert returned.json()["status"] == LoanStatus.RETURNED
    assert returned.json()["returned_timestamp"] is not None
    assert (
        client.post(f"/loans/{loan['id']}/return", headers=user_headers).status_code
        == 409
    )
    assert client.get("/loans/me", headers=user_headers).json() == [returned.json()]
    assert client.get(
        f"/books/{fixture.book_id}/loans", headers=admin_headers
    ).json() == [returned.json()]
    assert (
        client.delete(f"/books/{fixture.book_id}", headers=admin_headers).status_code
        == 409
    )

    with fixture.engine.connect() as connection:
        available_copies = connection.execute(
            select(Book.available_copies).where(Book.id == fixture.book_id)
        ).scalar_one()
        assert available_copies == 1


def test_concurrent_borrowing_allows_only_final_copy(loan_fixture: LoanFixture) -> None:
    fixture = loan_fixture
    headers = [
        {"Authorization": f"Bearer {create_access_token(fixture.user)}"},
        {"Authorization": f"Bearer {create_access_token(fixture.other_user)}"},
    ]

    async def borrow(request_headers: dict[str, str]) -> int:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/books/{fixture.book_id}/loans", headers=request_headers
            )
            return response.status_code

    async def borrow_concurrently() -> list[int]:
        return await asyncio.gather(
            *(borrow(request_headers) for request_headers in headers)
        )

    statuses = asyncio.run(borrow_concurrently())

    assert sorted(statuses) == [201, 409]
    with fixture.engine.connect() as connection:
        available_copies = connection.execute(
            select(Book.available_copies).where(Book.id == fixture.book_id)
        ).scalar_one()
        loan_count = connection.scalar(
            select(BookLoan.id).where(BookLoan.book_id == fixture.book_id)
        )
        assert available_copies == 0
        assert loan_count is not None
