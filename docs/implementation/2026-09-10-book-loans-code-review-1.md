# Code Review 1: Book Loans API

## Summary

The implementation follows the approved design in its model, migration, authorization boundaries, and basic transaction flow. No Critical or High findings were identified. The main remaining concerns are inventory-update invariants, lock ordering, and insufficient lifecycle/concurrency coverage.

## Findings

- **Severity:** Medium
  **Issue:** Book edits can reduce `total_copies` below the number of active loans. With one borrowed copy, an admin can set `total_copies` to zero because the handler only compares against `available_copies`; returning the loan then attempts to restore availability beyond the total-copy limit.
  **Evidence:** `backend/app/routers/books.py:96-103`
  **Recommendation:** Prevent `total_copies` from dropping below active loans plus available copies, with appropriate locking/counting, or define an explicit inventory-adjustment rule.

- **Severity:** Medium
  **Issue:** Return locks the loan before the book, while deletion can lock or operate on the book before the restrictive loan foreign key is checked. Concurrent return and delete operations can therefore deadlock or abort instead of producing the documented stable conflict.
  **Evidence:** `backend/app/routers/loans.py:43-62`; `backend/app/routers/books.py:125-133`
  **Recommendation:** Establish a consistent lock order, preferably book before loan for return, and add a concurrent return/delete test.

- **Severity:** Medium
  **Issue:** Loan behavior is effectively untested beyond authentication and role gates. Borrowing, duplicate prevention, availability mutation, return lifecycle, ownership, ordering, admin results, deletion conflicts, timestamps, and concurrent final-copy behavior lack endpoint tests.
  **Evidence:** `backend/tests/test_book_loans.py:24-40`
  **Recommendation:** Add PostgreSQL-backed API tests covering the design validation matrix, including concurrent borrowing and double returns.

- **Severity:** Medium
  **Issue:** Database validation is skipped without a configured PostgreSQL URL, and the executed suite did not validate migration execution or database constraint enforcement.
  **Evidence:** `backend/tests/test_database.py:103-141`; validation result `14 passed, 4 skipped`
  **Recommendation:** Run the full suite against an isolated migrated PostgreSQL database and verify lifecycle, timestamp, foreign-key, partial-unique-index, and downgrade behavior.

- **Severity:** Low
  **Issue:** The admin book-loan listing checks book existence and queries loans separately without locking. A concurrent deletion can produce `200 []` after the existence check rather than the specified `404`.
  **Evidence:** `backend/app/routers/books.py:198-211`
  **Recommendation:** Lock the book row during the existence check, or explicitly accept and test the weaker race semantics.

## Plan Compliance

- The model, migration, integer status mapping, named checks/FKs, restrictive history preservation, and three required partial indexes are present.
- Borrowing locks the book before checking availability and duplicate active loans, and mutates inventory and loan state in one transaction.
- User/admin authorization boundaries and persisted-user role checks follow the design.
- Return ownership, active-state checks, timestamp persistence, and inventory restoration are implemented.
- The loans router, OpenAPI document, README, and sample requests are updated.

## Validation Gaps

- PostgreSQL-backed tests were skipped because no test database was configured.
- Migration upgrade, downgrade/re-upgrade, schema inspection, lifecycle API behavior, and concurrency behavior were not demonstrated.

## Residual Risk

Aggregate title-level inventory intentionally cannot identify physical copies, as documented by the design. The Medium findings above should be addressed before production use.
