# Code Review 2: Book Loans API

## Summary

The second review confirms that the inventory invariant, book-first lock ordering, and admin listing race fixes are effective. One Medium migration-tooling issue and one Low authorization/locking issue remain.

## Findings

- **Severity:** Medium
  **Issue:** Alembic metadata discovery does not import `app.models`, so `Base.metadata` is incomplete for autogeneration and drift checks. `alembic check` can report existing tables and indexes as removed.
  **Evidence:** `backend/alembic/env.py:3-14`
  **Recommendation:** Import `app.models` in Alembic setup and run `uv run alembic check` against a migrated database.

- **Severity:** Low
  **Issue:** An authenticated user can cause another user's book row to be locked before ownership is checked by submitting a known loan ID.
  **Evidence:** `backend/app/routers/loans.py:43-64`
  **Recommendation:** Check ownership from the initial non-locking loan lookup before locking the book; then re-read the loan under lock for the authorized request.

## Prior-Finding Resolution

- Inventory invariant: fixed.
- Return/delete lock ordering: fixed.
- Admin listing race: fixed.
- Lifecycle and concurrency coverage: substantially improved.
- PostgreSQL validation: still environment-dependent; the fresh review run reported PostgreSQL tests skipped.

## Validation Gaps

- No demonstrated `alembic check` result.
- No test covers unauthorized return lock contention.
- Missing explicit tests for overdue-loan retention, response ordering, concurrent returns, and concurrent return/delete.

## Residual Risk

Aggregate title-level inventory remains intentionally unable to identify physical copies. The database does not independently enforce the relationship between available copies and active-loan count; application transaction paths maintain it.
