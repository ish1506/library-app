import asyncio
from unittest.mock import AsyncMock

from app.database import get_db
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.engine import make_url


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
