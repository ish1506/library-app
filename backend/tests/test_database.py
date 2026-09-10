import asyncio
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

import pytest
from app.database import get_db
from app.models.book import Book
from app.models.book_loan import BookLoan, LoanStatus
from app.models.user import Role, User
from app.routers.books import book_search_vector
from sqlalchemy import create_engine, delete, func, insert, inspect, select
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError


def test_postgresql_database_has_users_table(database_url: str) -> None:
    engine = create_engine(database_url)
    try:
        assert "users" in inspect(engine).get_table_names()
        columns = {column["name"] for column in inspect(engine).get_columns("users")}
        assert columns == {"id", "username", "password_hash", "role"}
        assert make_url(database_url).get_backend_name() == "postgresql"
    finally:
        engine.dispose()


def test_async_database_session_queries_and_closes(database_url: str) -> None:
    async def exercise_session() -> None:
        db_generator = get_db()
        db = await anext(db_generator)
        db.close = AsyncMock(wraps=db.close)

        try:
            assert await db.scalar(select(1)) == 1
        finally:
            await db_generator.aclose()

        db.close.assert_awaited_once()

    assert make_url(database_url).drivername == "postgresql+psycopg"
    asyncio.run(exercise_session())


def test_books_schema_persists_values_and_enforces_constraints(
    database_url: str,
) -> None:
    engine = create_engine(database_url)
    connection = engine.connect()
    transaction = connection.begin()
    try:
        isbn = f"978{uuid4().int % 10_000_000_000:010d}"
        columns = {column["name"] for column in inspect(engine).get_columns("books")}
        assert columns == {
            "id",
            "title",
            "author",
            "date",
            "isbn",
            "loan_duration_days",
            "total_copies",
            "available_copies",
        }

        result = connection.execute(
            insert(Book).values(
                title="A Book",
                author="An Author",
                date=1_700_000_000,
                isbn=isbn,
                loan_duration_days=14,
                total_copies=2,
                available_copies=2,
            )
        )
        assert result.inserted_primary_key[0]

        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(
                insert(Book).values(
                    title="Duplicate",
                    author="An Author",
                    date=1_700_000_000,
                    isbn=isbn,
                    loan_duration_days=14,
                    total_copies=2,
                    available_copies=2,
                )
            )

        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(
                insert(Book).values(
                    title="Invalid inventory",
                    author="An Author",
                    date=1_700_000_000,
                    isbn="9780306406157",
                    loan_duration_days=0,
                    total_copies=1,
                    available_copies=2,
                )
            )
    finally:
        transaction.rollback()
        connection.close()
        engine.dispose()


def test_book_loans_schema_has_constraints_and_partial_indexes(
    database_url: str,
) -> None:
    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)
        assert {column["name"] for column in inspector.get_columns("book_loans")} == {
            "id",
            "book_id",
            "user_id",
            "loan_timestamp",
            "due_at_timestamp",
            "returned_timestamp",
            "status",
        }
        assert {
            constraint["name"]
            for constraint in inspector.get_check_constraints("book_loans")
        } == {
            "ck_book_loans_status_valid",
            "ck_book_loans_due_at_after_loan",
            "ck_book_loans_lifecycle_consistent",
        }
        indexes = {index["name"] for index in inspector.get_indexes("book_loans")}
        assert indexes == {
            "uq_book_loans_active_user_book",
            "ix_book_loans_active_user_timestamp",
            "ix_book_loans_active_book_timestamp",
        }
        foreign_keys = {
            foreign_key["name"]
            for foreign_key in inspector.get_foreign_keys("book_loans")
        }
        assert foreign_keys == {
            "fk_book_loans_book_id_books",
            "fk_book_loans_user_id_users",
        }
    finally:
        engine.dispose()


def test_book_loans_constraints_preserve_lifecycle_and_history(
    database_url: str,
) -> None:
    engine = create_engine(database_url)
    connection = engine.connect()
    transaction = connection.begin()
    try:
        user_id = connection.execute(
            insert(User)
            .values(
                username=f"loan-test-{uuid4().hex}",
                password_hash="hash",
                role=Role.USER,
            )
            .returning(User.id)
        ).scalar_one()
        book_id = connection.execute(
            insert(Book)
            .values(
                title="Loan Constraint Book",
                author="An Author",
                date=1_700_000_000,
                isbn=f"978{uuid4().int % 10_000_000_000:010d}",
                loan_duration_days=14,
                total_copies=1,
                available_copies=0,
            )
            .returning(Book.id)
        ).scalar_one()
        loan_id = connection.execute(
            insert(BookLoan)
            .values(
                book_id=book_id,
                user_id=user_id,
                loan_timestamp=1_700_000_000,
                due_at_timestamp=1_700_000_000 + 86_400,
                status=LoanStatus.BORROWED,
            )
            .returning(BookLoan.id)
        ).scalar_one()
        assert loan_id

        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(
                insert(BookLoan).values(
                    book_id=book_id,
                    user_id=user_id,
                    loan_timestamp=1_700_000_001,
                    due_at_timestamp=1_700_000_002,
                    status=LoanStatus.BORROWED,
                )
            )
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(
                insert(BookLoan).values(
                    book_id=book_id,
                    user_id=user_id,
                    loan_timestamp=1_700_000_000,
                    due_at_timestamp=1_699_999_999,
                    status=LoanStatus.BORROWED,
                )
            )
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(
                insert(BookLoan).values(
                    book_id=book_id,
                    user_id=user_id,
                    loan_timestamp=1_700_000_000,
                    due_at_timestamp=1_700_000_001,
                    status=LoanStatus.BORROWED,
                    returned_timestamp=1_700_000_002,
                )
            )
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(delete(Book).where(Book.id == book_id))
    finally:
        transaction.rollback()
        connection.close()
        engine.dispose()


def test_books_search_indexes_and_predicates(database_url: str) -> None:
    engine = create_engine(database_url)
    connection = engine.connect()
    transaction = connection.begin()
    try:
        indexes = {index["name"] for index in inspect(engine).get_indexes("books")}
        assert {"ix_books_title_author_search", "ix_books_date"} <= indexes

        connection.execute(
            insert(Book),
            [
                {
                    "title": "The Left Hand of Darkness",
                    "author": "Ursula K. Le Guin",
                    "date": 0,
                    "isbn": "9780441478125",
                    "loan_duration_days": 14,
                    "total_copies": 1,
                    "available_copies": 1,
                },
                {
                    "title": "The Dispossessed",
                    "author": "Ursula K. Le Guin",
                    "date": 1,
                    "isbn": "9780151554658",
                    "loan_duration_days": 14,
                    "total_copies": 1,
                    "available_copies": 1,
                },
            ],
        )
        search = book_search_vector()
        text_results = connection.execute(
            select(Book).where(
                search.op("@@")(
                    func.websearch_to_tsquery("simple", "dispossessed")
                )
            )
        ).scalars().all()
        assert [book.title for book in text_results] == ["The Dispossessed"]

        date_results = connection.execute(
            select(Book).where(Book.date >= 1, Book.date <= 1)
        ).scalars().all()
        assert [book.title for book in date_results] == ["The Dispossessed"]
    finally:
        transaction.rollback()
        connection.close()
        engine.dispose()
