# Code Review 1: Async Database Client Refactor

## Summary

The runtime query path was converted to SQLAlchemy's async API and the configured
`postgresql+psycopg` URL is accepted by both the async and sync engines. The
focused suite passes (`5 passed, 1 skipped`), but it uses only a fake async
session and does not validate the real psycopg connection path or the production
dependency lifecycle. Two medium-severity findings remain.

## Findings

- Severity: Medium
  Issue: The application never disposes the global async engine during shutdown.
  Evidence: `backend/app/database.py:18` creates `async_engine` globally, while
  `backend/main.py:4-10` defines no lifespan or shutdown handler that awaits
  `async_engine.dispose()`. `backend/app/database.py:30-32` closes each session,
  but that does not dispose the engine's connection pool.
  Recommendation: Add a FastAPI lifespan/shutdown hook that awaits
  `async_engine.dispose()`, and test that shutdown invokes it. Keep the per-request
  `AsyncSession` context manager as-is.

- Severity: Medium
  Issue: The tests do not verify the real async SQLAlchemy/psycopg path or the
  cleanup behavior of `get_db()`, so the central refactor can regress while the
  suite remains green.
  Evidence: `backend/tests/test_login.py:8-18` replaces `get_db` with a lambda
  returning `FakeSession`, and only `FakeSession.scalar()` is awaitable
  (`backend/tests/test_login.py:12-14`). No test executes
  `backend/app/database.py:30-32` or performs an async query through
  `AsyncSessionLocal`; `backend/tests/test_database.py:1-13` checks metadata with
  a synchronous engine only.
  Recommendation: Add an isolated PostgreSQL integration test using the actual
  `AsyncSessionLocal`/`get_db()` and `postgresql+psycopg`, covering a query and
  session cleanup. Retain the fake-session endpoint tests for API behavior, but
  do not treat them as async-driver validation.

## Plan Compliance

- `backend/app/database.py` uses `create_async_engine`, `AsyncSession`,
  `async_sessionmaker`, and an async generator dependency with `async with`.
- `backend/app/routers/auth.py` uses `async def`, `AsyncSession`, and awaits
  `scalar()`.
- A separate synchronous engine/session factory remains available for the seed
  helper, and Alembic remains synchronous.
- The psycopg dependency and URL format were preserved; no lockfile change was
  needed.
- Login behavior, response shape, schema, JWT claims, and password hashing were
  not changed by the reviewed async refactor.
- The plan's request-path sync-session requirement is met by the inspected route.
- The plan's clean async-engine shutdown validation is not met, and its real
  PostgreSQL async validation was not demonstrated.
- The staged README and `scripts/dev.sh`/`scripts/test.sh` changes were treated as
  pre-existing unrelated worktree changes, not attributed to this refactor.

## Validation Gaps

- `uv run pytest` passed with `5 passed, 1 skipped`; the PostgreSQL schema test was
  skipped because no test database was configured.
- No isolated `alembic upgrade head` run was performed against PostgreSQL.
- No seed-helper duplicate-user validation was performed against PostgreSQL.
- No live API login request was run against PostgreSQL.
- No async session cleanup or application shutdown disposal test exists.
- The psycopg driver was verified to construct both SQLAlchemy engines, but no
  real async connection or query was established.

## Residual Risk

The main remaining risk is production-only behavior: connection acquisition,
transaction rollback on request teardown, and pool disposal are not covered by
the passing fake-session tests. Argon2 password verification remains synchronous
and CPU-bound, as intentionally left outside this plan.
