import asyncio
from unittest.mock import AsyncMock

from app.database import get_db
from app.models.book import Book
from sqlalchemy import create_engine, insert, inspect, select
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
                isbn="9780441478125",
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
                    isbn="9780441478125",
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
