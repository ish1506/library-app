# Open Library Book Seed

## Goal

Create a one-time seed workflow that imports approximately 100 well-known books
from Open Library into the local `books` table. The workflow should produce a
reviewable CSV, normalize Open Library's edition-level search data into this
application's book shape, apply documented defaults for application-owned
fields, and load the result transactionally.

The import must be safe to re-run while developing, must not depend on the
public Books HTTP endpoints, and must seed each imported title with one
available physical copy.

## Current State

- The `books` table is created by
  `backend/alembic/versions/20260910_0002_create_books.py`.
- Migration `backend/alembic/versions/20260910_0003_allow_zero_total_copies.py`
  changes the copy constraint to `total_copies >= 0`; no new copy-constraint
  migration is needed.
- `BookCreate` requires `title`, `author`, `date`, `isbn`,
  `loan_duration_days`, and `total_copies`.
- Publication dates are stored as Unix timestamps in seconds. ISBNs are
  normalized to exactly 13 digits and are unique.
- Creating a book sets `available_copies` equal to `total_copies`.
- The Books API is admin-only for mutations, but a seed script can use the
  database directly and avoid authentication and HTTP overhead.
- Open Library asks clients not to use its APIs as a bulk backend. The workflow
  must identify itself with a `User-Agent`, respect rate limits, cache responses,
  and remain limited to the curated 100-book manifest.

## Decisions

- Keep a curated manifest of 100 famous book titles in the repository. The
  manifest is the source of truth for which books are seeded; "famous" is not
  inferred from an unbounded Open Library query.
- Use Open Library's JSON search endpoint to resolve each manifest title. Make
  requests sequentially, cache every raw response, identify the client with an
  application name and contact email, and retry transient failures with
  backoff. Do not scrape HTML or make per-work/edition follow-up requests.
- Select one edition per title using deterministic rules: prefer a result with
  an ISBN-13, prefer an exact or closest title match, then prefer the result
  with the most useful publication metadata. Record the selected Open Library
  key and source response in the raw cache for auditability.
- Extract the first valid ISBN-13 from the selected result. Skip and report a
  title if no ISBN-13 exists; never invent an ISBN because the database uses it
  as a unique bibliographic identifier.
- Use the first available author name. If the API has no author name, use
  `Unknown Author` so the required application field remains populated.
- Use `first_publish_year` or a parseable publication date when available. If
  the date is missing or unparseable, use Unix timestamp `0` (`1970-01-01T00:00:00Z`)
  as an explicit unknown-date sentinel.
- Set `loan_duration_days` to `14` for every imported book unless the seed
  manifest explicitly overrides it.
- Set `total_copies` to `1` and `available_copies` to `1` for every imported
  book. This seed represents one available physical copy per title.
- Treat title and ISBN as non-defaultable required values. Skip malformed or
  duplicate rows and report them before any database commit.
- Use a CSV as the review/import artifact, but retain raw JSON responses as the
  acquisition artifact. CSV is not used as the canonical representation of
  Open Library's nested data.
- Insert directly with the existing SQLAlchemy database configuration in one
  transaction. On rerun, use normalized ISBN as the idempotency key and skip
  already-seeded ISBNs rather than creating duplicates or overwriting catalogue
  edits.

## Diagram

```mermaid
flowchart LR
    A[100-title manifest] --> B[Open Library search JSON]
    B --> C[Cached raw responses]
    C --> D[Normalize and validate]
    D --> E[Reviewable CSV]
    E --> F[Transactional DB import]
    F --> G[books table]
```

## Implementation Steps

1. Add a manifest file containing 100 curated titles and optional per-title
   overrides. Keep titles unique and stable so the seed can be audited and
   repeated.
2. Add a seed command under `backend/scripts/` with separate acquisition,
   normalization, validation, CSV export, and database-load stages. Support:
   `--fetch`, `--csv PATH`, `--dry-run`, and `--load` modes so fetching and
   loading are not inseparably coupled.
3. During acquisition, query Open Library's JSON search endpoint for each
   manifest title, send the required identifying headers, respect the documented
   rate limit, and write responses under a local ignored seed-cache directory.
   A cached response should be reused unless an explicit refresh option is
   supplied.
4. Normalize each selected result to these CSV columns:
   `source_key`, `title`, `author`, `date`, `isbn`, `loan_duration_days`,
   `total_copies`, `available_copies`.
5. Validate the complete CSV before loading. Check required values, ISO/date
   conversion, 13-digit ISBN normalization, unique ISBNs, nonnegative copies,
   and the expected row count. Print skipped titles and reasons; do not partially
   load an invalid batch.
6. Review the generated CSV as the explicit approval point. The default output
   should be deterministic apart from source data changes and should include a
   summary of imported, skipped, duplicate, and defaulted fields.
7. With `--load`, open one database transaction, insert only ISBNs not already
   present, set `available_copies` to `total_copies`, and commit only after all
   rows pass validation. Roll back the entire batch on an unexpected database
   error.
8. Add focused tests for date conversion, ISBN selection/normalization,
   deterministic result selection, default values, duplicate handling, dry-run
   behavior, and transaction failure behavior. Use mocked Open Library responses;
   tests must not call the external API.
9. Document the exact command, expected environment variables, cache location,
   defaults, and rerun behavior in the backend README.

## Files and Interfaces

- `backend/seed_data/famous_books.txt` or `.json`: curated 100-title manifest.
- `backend/scripts/seed_books.py`: fetch, normalize, export, validate, and load
  command-line workflow.
- `backend/seed_cache/`: local raw API responses; add to `.gitignore` and do not
  commit generated responses unless explicitly desired for fixtures.
- `backend/tests/test_seed_books.py`: unit and integration-style tests using
  mocked API responses and the test database conventions already in the repo.
- `backend/README.md`: operational instructions and field-default documentation.
- Existing migration `20260910_0003_allow_zero_total_copies.py`: retain and
  verify; do not create a replacement migration for the already-supported zero.

The script should expose a small internal model or dictionary with the exact
CSV shape above. The database loader should use the existing SQLAlchemy models
and configuration rather than duplicating table definitions.

## Validation

- Run the backend test suite with `./scripts/test.sh` from `backend`.
- Run the seed in fetch/CSV dry-run mode and confirm it makes no database
  changes.
- Inspect the CSV and confirm every loaded row has a title, author, normalized
   ISBN-13, date integer, `loan_duration_days = 14`, and
   `total_copies = available_copies = 1`.
- Run the loader against a migrated disposable database and confirm the row
  count, unique ISBNs, zero-copy values, and stored date values.
- Run the loader a second time and confirm no duplicate rows are inserted and
  existing rows are not overwritten.
- Include at least one fixture with a missing author/date and confirm the
  documented defaults are applied, plus one fixture without ISBN-13 and confirm
  it is skipped and reported.

## Risks and Open Questions

- Open Library search results can change over time and may return a different
  edition or ISBN. The cached raw responses and generated CSV provide a stable
  review point for this one-time seed.
- A title may have multiple valid editions. This plan intentionally imports one
  ISBN-bearing edition per manifest title rather than modelling works and
  editions separately.
- The date sentinel `0` is technically valid in the current integer column but
  is not a real publication date. A future schema could make publication date
  nullable; that is outside this seed task.
- Books without ISBN-13 are skipped rather than assigned fake identifiers, so
  the final imported count may be below 100. The command should report the
  shortfall clearly.
- The import intentionally does not seed loans, users, reservations, covers,
  subjects, or Open Library identifiers in the `books` schema.

## Handoff Notes

- The zero-copy requirement is already represented by migration `20260910_0003`.
- Do not use the public `POST /books` endpoint for the batch; it adds HTTP and
  authentication overhead and is not the appropriate bulk-import boundary.
- Do not silently substitute a different source or invent ISBNs to force the
  result to exactly 100 rows.
- The plan assumes the seed is a developer/initial-environment operation, not
  a recurring synchronization job.
