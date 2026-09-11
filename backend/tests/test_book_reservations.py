import asyncio
from collections.abc import Generator
from dataclasses import dataclass
from time import time
from uuid import uuid4

import pytest
from app.database import get_db
from app.models.book import Book
from app.models.book_loan import BookLoan
from app.models.book_reservation import BookReservation
from app.models.enums import ReservationStatus, Role
from app.models.notification import Notification
from app.models.user import User
from app.services.auth import create_access_token
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from main import app
from sqlalchemy import Engine, create_engine, delete, insert, inspect, select, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine


class AuthSession:
    def __init__(self, *users: User) -> None:
        self.users = {user.id: user for user in users}

    async def get(self, model: object, item_id: int) -> User | None:
        return self.users.get(item_id)


@dataclass
class ReservationFixture:
    engine: Engine
    async_engine: AsyncEngine
    book_id: int
    users: list[User]


@pytest.fixture
def reservation_fixture(database_url: str) -> Generator[ReservationFixture, None, None]:
    engine = create_engine(database_url)
    async_engine = create_async_engine(database_url)
    suffix = uuid4().hex[:10]
    users = [
        User(
            username=f"reservation-{suffix}-{index}",
            password_hash="hash",
            role=Role.USER,
        )
        for index in range(4)
    ]
    isbn = f"978{uuid4().int % 10_000_000_000:010d}"
    try:
        with engine.begin() as connection:
            for user in users:
                user.id = connection.execute(
                    insert(User)
                    .values(
                        username=user.username,
                        password_hash=user.password_hash,
                        role=user.role,
                    )
                    .returning(User.id)
                ).scalar_one()
            book_id = connection.execute(
                insert(Book)
                .values(
                    title="Reservation Test Book",
                    author="Test Author",
                    date=1_700_000_000,
                    isbn=isbn,
                    loan_duration_days=14,
                    total_copies=1,
                    available_copies=1,
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
    fixture = ReservationFixture(engine, async_engine, book_id, users)
    try:
        yield fixture
    finally:
        app.dependency_overrides.clear()
        with engine.begin() as connection:
            connection.execute(
                delete(Notification).where(
                    Notification.user_id.in_([u.id for u in users])
                )
            )
            connection.execute(
                delete(BookReservation).where(BookReservation.book_id == book_id)
            )
            connection.execute(delete(BookLoan).where(BookLoan.book_id == book_id))
            connection.execute(delete(Book).where(Book.id == book_id))
            connection.execute(delete(User).where(User.id.in_([u.id for u in users])))
        asyncio.run(async_engine.dispose())
        engine.dispose()


def headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user)}"}


def test_reservation_routes_require_user_role() -> None:
    user = User(id=1, username="user", password_hash="hash", role=Role.USER)
    admin = User(id=2, username="admin", password_hash="hash", role=Role.ADMIN)
    app.dependency_overrides[get_db] = lambda: AuthSession(user, admin)
    client = TestClient(app)
    assert client.get("/reservations/me").status_code == 401
    assert client.get("/notifications").status_code == 401
    assert client.get("/reservations/me", headers=headers(admin)).status_code == 403
    assert client.get("/notifications", headers=headers(admin)).status_code == 403
    app.dependency_overrides.clear()


def test_reservation_schema_constraints_and_indexes(database_url: str) -> None:
    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)
        assert {"book_reservations", "notifications"} <= set(
            inspector.get_table_names()
        )
        reservation_indexes = {
            index["name"] for index in inspector.get_indexes("book_reservations")
        }
        notification_indexes = {
            index["name"] for index in inspector.get_indexes("notifications")
        }
        assert {
            "uq_book_reservations_active_user_book",
            "ix_book_reservations_pending_queue",
            "ix_book_reservations_ready_expiry",
            "ix_book_reservations_book_status",
        } <= reservation_indexes
        assert {
            "ix_notifications_user_unread_created",
            "uq_notifications_reservation_ready",
        } <= notification_indexes
        reservation_checks = {
            check["name"]
            for check in inspector.get_check_constraints("book_reservations")
        }
        notification_checks = {
            check["name"] for check in inspector.get_check_constraints("notifications")
        }
        assert {
            "ck_book_reservations_status_valid",
            "ck_book_reservations_lifecycle_consistent",
        } <= reservation_checks
        assert "ck_notifications_type_valid" in notification_checks
    finally:
        engine.dispose()


def test_reservation_lifecycle_notifications_and_expiry(
    reservation_fixture: ReservationFixture,
) -> None:
    fixture = reservation_fixture
    client = TestClient(app)
    first, second = fixture.users[:2]
    borrowed = client.post(f"/books/{fixture.book_id}/loans", headers=headers(first))
    assert borrowed.status_code == 201
    reservation = client.post(
        f"/books/{fixture.book_id}/reservations", headers=headers(second)
    )
    assert reservation.status_code == 201
    reservation_id = reservation.json()["id"]
    assert (
        client.post(
            f"/books/{fixture.book_id}/reservations", headers=headers(second)
        ).status_code
        == 409
    )

    returned = client.post(
        f"/loans/{borrowed.json()['id']}/return", headers=headers(first)
    )
    assert returned.status_code == 200
    listed = client.get("/notifications", headers=headers(second)).json()
    assert len(listed) == 1
    assert listed[0]["reservation_id"] == reservation_id
    assert (
        client.patch(
            f"/notifications/{listed[0]['id']}/read", headers=headers(second)
        ).status_code
        == 200
    )

    with fixture.engine.begin() as connection:
        connection.execute(
            update(BookReservation)
            .where(BookReservation.id == reservation_id)
            .values(expires_at_timestamp=int(time()) - 1)
        )
    assert (
        client.post(
            f"/reservations/{reservation_id}/confirm", headers=headers(second)
        ).status_code
        == 409
    )
    with fixture.engine.connect() as connection:
        reservation_status = connection.scalar(
            select(BookReservation.status).where(BookReservation.id == reservation_id)
        )
        available = connection.scalar(
            select(Book.available_copies).where(Book.id == fixture.book_id)
        )
    assert reservation_status == ReservationStatus.EXPIRED
    assert available == 1


def test_concurrent_reservations_allocate_one_queue_slot(
    reservation_fixture: ReservationFixture,
) -> None:
    fixture = reservation_fixture
    first, second, third = fixture.users[:3]
    client = TestClient(app)
    borrowed = client.post(f"/books/{fixture.book_id}/loans", headers=headers(first))
    assert borrowed.status_code == 201

    async def reserve(user: User) -> int:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as async_client:
            response = await async_client.post(
                f"/books/{fixture.book_id}/reservations", headers=headers(user)
            )
            return response.status_code

    async def reserve_concurrently() -> list[int]:
        return await asyncio.gather(reserve(second), reserve(third))

    statuses = asyncio.run(reserve_concurrently())
    assert sorted(statuses) == [201, 409]
