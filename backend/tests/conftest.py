import os

import pytest


@pytest.fixture
def database_url() -> str:
    value = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not value or not value.startswith("postgresql"):
        pytest.skip("PostgreSQL test database is not configured")
    return value
