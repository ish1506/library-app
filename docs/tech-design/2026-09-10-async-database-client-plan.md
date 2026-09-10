# Async Database Client Refactor Plan

## Goal

Refactor request-time database access to use SQLAlchemy's asyncio API with the
existing `psycopg` 3 dependency. The login endpoint should perform its
PostgreSQL query without blocking the event loop, while preserving its current
API behavior and schema.

## Current State

- `backend/app/database.py` creates a synchronous SQLAlchemy engine and
  `Session` factory.
- `backend/app/routers/auth.py` has one database-backed endpoint,
  `POST /auth/login`, implemented as a synchronous function.
- `backend/scripts/seed_user.py` uses the synchronous session factory.
- `backend/alembic/env.py` and `backend/tests/test_database.py` use synchronous
  SQLAlchemy APIs.
- `psycopg[binary]` and SQLAlchemy are already project dependencies.
- Existing worktree changes are part of the user-management implementation;
  do not overwrite unrelated changes.

## Decisions

- Use SQLAlchemy `create_async_engine`, `AsyncSession`, and
  `async_sessionmaker` for application request handling.
- Keep the existing `postgresql+psycopg://` URL format. Psycopg 3 supports the
  async SQLAlchemy dialect through `create_async_engine`.
- Do not add `asyncpg` unless a later performance or compatibility requirement
  justifies changing drivers.
- Keep Alembic synchronous. Maintain a synchronous engine path for migrations,
  the seed CLI, and database metadata inspection rather than expanding the
  async refactor unnecessarily.
- Preserve `expire_on_commit=False`, current transaction boundaries, login
  response shape, and error behavior.

## Implementation Steps

1. Update `app/database.py` to create the async engine and async session
   factory, and expose `get_db()` as an async generator that closes each
   `AsyncSession` with `async with`.
2. Update `app/routers/auth.py` so `login()` is `async def`, accepts an
   `AsyncSession`, and awaits the scalar query.
3. Add a separate synchronous engine/session factory for tooling, or a small
   sync-engine helper derived from the same configured URL. Use it in
   `scripts/seed_user.py` and keep Alembic configured against the sync URL.
4. Update login test doubles and endpoint tests so fake database operations are
   awaitable. Keep persistence/inspection tests synchronous where they test
   migrations and schema metadata.
5. Review all database imports and search for synchronous session use in
   application request code. There should be no remaining sync session
   dependency in FastAPI routes.
6. Regenerate the lockfile only if dependency metadata changes. No dependency
   change is expected for the initial implementation.

## Files and Interfaces

- `backend/app/database.py`: async runtime engine/session dependency plus sync
  tooling access.
- `backend/app/routers/auth.py`: async login handler and `AsyncSession` type.
- `backend/scripts/seed_user.py`: continue using the sync tooling session.
- `backend/alembic/env.py`: remain synchronous and migration-compatible.
- `backend/tests/test_login.py`: awaitable fake session and async-path coverage.
- `backend/tests/test_database.py`: retain sync inspection or explicitly test
  the sync tooling engine.
- `backend/pyproject.toml`: likely no change; verify `psycopg[binary]` remains
  present.
- `backend/README.md`: document that runtime DB access is async if the setup
  instructions currently describe the client behavior.

## Validation

- From `backend/`, run `uv run pytest`.
- Run `uv run alembic upgrade head` against an isolated PostgreSQL database.
- Run the seed helper and verify it can create and reject duplicate users.
- Start the API with `uv run fastapi dev main.py` and verify `/health` and
  successful/failed `/auth/login` requests.
- Confirm no request path calls synchronous SQLAlchemy session methods.
- Confirm the application can open and dispose the async engine cleanly during
  normal shutdown or test teardown.

## Risks and Open Questions

- Argon2 password verification remains synchronous and CPU-bound. It is outside
  this database refactor; revisit it separately if login throughput requires
  moving hashing work to a thread pool.
- Async database tests may require an async test fixture only if real async
  session behavior is tested directly. The current endpoint tests can continue
  using FastAPI's `TestClient` with an awaitable fake session.
- A separate sync tooling engine is intentionally retained to avoid making
  migrations and one-off CLI commands depend on an event loop.

## Handoff Notes

- Implement the smallest change that affects runtime request database I/O.
- Do not alter the users table, authentication contract, JWT claims, or password
  hashing settings.
- Prefer the existing psycopg driver over a driver migration to `asyncpg`.
