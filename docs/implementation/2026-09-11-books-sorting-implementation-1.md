# Books Sorting Backend Implementation

## Files

- Extended `BookListQuery` with validated `sort_by` and `sort_order` enums,
  case normalization, and cross-field validation.
- Added an allowlisted SQLAlchemy sort-expression mapping in the books router.
- Added request-level coverage for all sort fields/directions, case-insensitive
  text ordering, ID tie-breaking, search precedence, and invalid parameters.
- Added PostgreSQL-backed expression ordering coverage in
  `backend/tests/test_database.py`.
- Updated backend usage documentation, sample requests, and
  `docs/openapi.json`.

## Validation

Explicit sorts use `lower(Book.title)` or `lower(Book.author)`, numeric
`Book.date`, and ascending `Book.id` as the final key. Invalid enum values and
`sort_order` without `sort_by` return `422`. Without `sort_by`, existing ID
ordering and search relevance ordering remain unchanged.

## Deviations

None. No indexes or migrations were added because the approved design defers
that decision until query-plan evidence exists.

## Blockers and Assumptions

The PostgreSQL-backed test is skipped when no test database URL is configured.
The public values are normalized case-insensitively before enum validation;
responses and OpenAPI continue to expose the lowercase contract values.
