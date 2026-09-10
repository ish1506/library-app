from sqlalchemy import create_engine, inspect
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
