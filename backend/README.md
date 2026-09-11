# Library Backend

## Requirements

- Python 3.12 or later
- PostgreSQL 14 or later
- [uv](https://docs.astral.sh/uv/)

## Run locally

```bash
uv sync
cp .env.example .env
# Set DATABASE_URL to a PostgreSQL database and JWT_SECRET_KEY to a random secret.
uv run alembic upgrade head
./scripts/dev.sh
```

The API is available at `http://127.0.0.1:8000`, with interactive documentation at `/docs` and a health check at `/health`.
Request-time database access uses SQLAlchemy's async API with the psycopg driver;
Alembic and the local seed helper use a separate synchronous client.

Refresh the checked-in OpenAPI document from the application definition with:

```bash
uv run python scripts/refresh_openapi.py
```

The development script accepts the same additional arguments as the FastAPI CLI,
for example `./scripts/dev.sh --port 8001`. It can be run from the `backend`
directory or by providing its path from another directory.

## Run tests

Run the test suite from the `backend` directory:

```bash
./scripts/test.sh
```

The service and API tests run without a database. The PostgreSQL schema test is
skipped unless `TEST_DATABASE_URL` or `DATABASE_URL` is set. To run it, point
`TEST_DATABASE_URL` at a migrated test database:

```bash
TEST_DATABASE_URL='postgresql+psycopg://library_app:password@localhost:5432/library_db' ./scripts/test.sh
```

Additional pytest arguments can be passed through, such as
`./scripts/test.sh tests/test_login.py -q`.

## Configuration

`DATABASE_URL` must be a PostgreSQL SQLAlchemy URL, for example
`postgresql+psycopg://library_app:password@localhost:5432/library_db`.
`JWT_SECRET_KEY` must be a cryptographically random signing secret. Both values
are required. `.env` is local-only and must not be committed; use `.env.example`
as the safe template.

Reservations use `RESERVATION_HOLD_SECONDS` for the duration of a ready hold;
the default is `86400` seconds and the value must be positive. The in-process
expiry worker checks every `RESERVATION_WORKER_INTERVAL_SECONDS` seconds,
defaulting to `60`. Each reservation mutation also expires relevant holds, so
correctness does not depend on the worker. A multi-process deployment needs a
database-backed scheduler or lease.

## Provision an account

Accounts are provisioned locally with the non-public seed helper, not through an
API route:

```bash
uv run python scripts/seed_user.py alice --password 'password' --role USER
uv run python scripts/seed_user.py admin --password 'admin' --role ADMIN
```

The helper rejects duplicate usernames and stores only an Argon2id password hash.

## Seed the book catalogue

The book seed is a curated manifest of exactly 100 unique famous titles. The
script searches Open Library sequentially and stores each raw JSON response in
the ignored `backend/seed_cache/` directory. Set `OPEN_LIBRARY_CONTACT_EMAIL`
to a real contact address before fetching; it is included in the identifying
User-Agent. The default is `library-app@example.com`. Requests are rate-limited
to 0.2 seconds and retried with exponential backoff.

From the `backend` directory, fetch and create the default normalized CSV:

```bash
OPEN_LIBRARY_CONTACT_EMAIL='you@example.com' uv run python scripts/seed_books.py --fetch
```

Use `--refresh --fetch` to ignore cached responses. Export to a specific CSV
with `--csv PATH` (it fetches missing responses and reuses the cache):

```bash
uv run python scripts/seed_books.py --csv /tmp/library-books.csv
```

The CSV columns are `source_key,title,author,date,isbn,loan_duration_days,
total_copies,available_copies`. Missing authors default to `Unknown Author`,
missing dates to Unix timestamp `0`, and inventory defaults to a 14-day loan,
one total copy, and one available copy. Entries without a valid ISBN-13 or
with duplicate ISBN-13 values are reported and skipped. Dates outside the
existing PostgreSQL `BIGINT` timestamp range also use the `0` sentinel. The
batch is validated before any database write.

Load the default CSV transactionally and idempotently. Existing ISBNs are not
updated. `--dry-run` validates and reports the number that would be inserted:

```bash
uv run python scripts/seed_books.py --load
uv run python scripts/seed_books.py --load --dry-run
uv run python scripts/seed_books.py --load --csv /tmp/library-books.csv
```

Rerun `--load` safely after a failed or completed run. A transaction rollback
leaves all rows unchanged; rerunning inserts only ISBNs that are still absent.

## Login

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"password"}'
```

Successful responses contain a one-hour HS256 bearer access token. Invalid
usernames and passwords return the same `401 Invalid username or password`
response.

## Books catalogue

All catalogue endpoints require an `ADMIN` bearer token. Missing, malformed,
expired, or stale tokens return `401` with `WWW-Authenticate: Bearer`; valid
`USER` tokens return `403`.

```bash
curl -X POST http://127.0.0.1:8000/books \
  -H 'Authorization: Bearer <admin-token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "The Left Hand of Darkness",
    "author": "Ursula K. Le Guin",
    "date": "1969-03-01T00:00:00-08:00",
    "isbn": "978-0-441-47812-5",
    "loan_duration_days": 14,
    "total_copies": 3
  }'
```

`GET /books` lists the catalogue and accepts optional `q`, `date_from`,
`date_to`, `sort_by`, and `sort_order` query parameters. `q` searches title
and author terms, while the inclusive date bounds accept offset-aware ISO 8601
datetimes. `sort_by` accepts `title`, `author`, or `date`; `sort_order` accepts
`asc` or `desc` and requires `sort_by`. Title and author sorting is
case-insensitive. Without an explicit sort, results use ID ascending, or
relevance descending then ID ascending for searches. For example:

```bash
curl --get 'http://127.0.0.1:8000/books' \
  --data-urlencode 'q=le guin' \
  --data-urlencode 'date_from=1960-01-01T00:00:00Z' \
  --data-urlencode 'date_to=1970-12-31T23:59:59Z' \
  --data-urlencode 'sort_by=title' \
  --data-urlencode 'sort_order=asc' \
  -H 'Authorization: Bearer <admin-token>'
```

`GET /books/{book_id}` returns one book.
`PATCH /books/{book_id}` accepts any subset of `title`, `author`, `date`,
`isbn`, `loan_duration_days`, and `total_copies`; `DELETE /books/{book_id}`
hard-deletes a book. Creation returns `201`, deletion returns `204`, and
duplicate ISBN-13 values return `409 ISBN already exists`. Inventory reductions
cannot set `total_copies` below the sum of active and available copies.

Publication dates are accepted as offset-aware ISO 8601 datetimes and are
stored and returned as Unix timestamps in seconds. ISBNs accept only 13 digits;
spaces and hyphens are removed before storage, so equivalent formatted ISBN-13
values conflict. ISBN-10 values and checksum validation are out of scope.

## Sample requests

Run the development server, then copy a request from
`sample_requests/books.txt` into Postman or a terminal. Define Postman
variables for `baseUrl`, `username`, `password`, `adminToken`, and `bookId`.

```bash
cat sample_requests/books.txt
```

The create example uses zero total copies; modify the request body for another
supported payload.

## Book loans

Borrowing and returning require a `USER` bearer token. `POST
/books/{book_id}/loans` creates a title-level loan and returns `201`; `GET
/loans/me` lists only the caller's active loans; and `POST
/loans/{loan_id}/return` returns one of the caller's active loans. An `ADMIN`
can use `GET /books/{book_id}/loans` to list that book's active loans and
borrower IDs. These endpoints return Unix UTC timestamps in seconds and use
status `1` for `BORROWED` and `2` for `RETURNED`.

Unavailable books and duplicate active loans return `409`. A returned loan
cannot be returned again, and a book with loan history cannot be deleted.
Overdue loans remain active until returned. Reservations, renewal, late fees,
and per-copy inventory are not supported by the loan endpoints.

```bash
curl -X POST http://127.0.0.1:8000/books/$bookId/loans \
  -H 'Authorization: Bearer <user-token>'

curl http://127.0.0.1:8000/loans/me \
  -H 'Authorization: Bearer <user-token>'

curl -X POST http://127.0.0.1:8000/loans/$loanId/return \
  -H 'Authorization: Bearer <user-token>'

curl http://127.0.0.1:8000/books/$bookId/loans \
  -H 'Authorization: Bearer <admin-token>'
```

## Reservations and notifications

Reservations require a `USER` bearer token and are available only when a title
has no immediately available copy. A user cannot reserve a title they already
loan or reserve, and the active queue is limited to the number of active loans
for that title. These conflicts return `409`. Reservations are served in
creation order. Returning a loan promotes the oldest pending reservation to a
one-day ready hold and creates one unread in-app notification.

```bash
curl -X POST http://127.0.0.1:8000/books/$bookId/reservations \
  -H 'Authorization: Bearer <user-token>'

curl http://127.0.0.1:8000/reservations/me \
  -H 'Authorization: Bearer <user-token>'

curl -X POST http://127.0.0.1:8000/reservations/$reservationId/confirm \
  -H 'Authorization: Bearer <user-token>'

curl -X DELETE http://127.0.0.1:8000/reservations/$reservationId \
  -H 'Authorization: Bearer <user-token>'

curl --get 'http://127.0.0.1:8000/notifications?unread_only=true&limit=50' \
  -H 'Authorization: Bearer <user-token>'

curl -X PATCH http://127.0.0.1:8000/notifications/$notificationId/read \
  -H 'Authorization: Bearer <user-token>'
```

`GET /notifications` is caller-scoped, newest-first, and bounded to at most
100 results per request. `unread_only` defaults to `true`. Confirming a ready
reservation creates the loan without decrementing `available_copies`, because
the ready hold already owns that capacity. Cancelling or expiring a ready hold
promotes the next pending reservation or releases one available copy. Terminal
actions return `409`; admin and unauthenticated callers receive the standard
`403` and `401` responses respectively.
