# Library App

A full-stack library application for managing a book catalogue, lending titles,
calculating late fees, and reserving unavailable books.

## Supported Features

### Catalogue Management

- Authenticated users can browse, search, filter, sort, and view books.
- Administrators can add, edit, and remove books.
- Inventory is maintained as total and available copies for each title.
- A curated 100-book catalogue can be imported from Open Library.

### Lending

- Members can borrow available titles and return their own active loans.
- Members can review active and returned loan history, including due dates.
- Administrators can inspect the loan history for a title.
- Late fees accrue for complete 24-hour periods after a loan becomes overdue and
  are frozen when the title is returned.

### Reservations and Notifications

- Members can reserve an unavailable title when a reservation slot is available.
- A returned copy is held for its pending reservation for a configurable period.
- Members receive an in-app notification when their reservation becomes ready.
- Ready reservations can be confirmed or cancelled and expire automatically.

### User Management

- Users sign in with a username and password.
- Role-based authorization separates member and administrator actions.
- Development accounts are provisioned with a command-line seed utility.

## Technology

- React 19, TypeScript, and Vite
- FastAPI, SQLAlchemy, and Alembic
- PostgreSQL

## Development Setup

### Prerequisites

- Python 3.12 or later
- Node.js 22.12 or later and npm
- PostgreSQL 14 or later
- [uv](https://docs.astral.sh/uv/)

### Install Dependencies

Install the backend and frontend dependencies, then install the Git pre-commit
hook from the repository root:

```bash
cd backend
uv sync
cd ../frontend
npm install
cd ..
uvx pre-commit install
```

The pre-commit hook formats backend Python with Ruff and frontend source with
Biome during `git commit`. Run the hooks manually against all files with:

```bash
uvx pre-commit run --all-files
```

If a formatter changes files, stage the changes and commit again.

### Configure the Backend

Create a PostgreSQL database, then configure and migrate the backend:

```bash
cd backend
cp .env.example .env
# Set DATABASE_URL and replace JWT_SECRET_KEY with a random secret in .env.
uv run alembic upgrade head
uv run python scripts/seed_user.py alice --password 'password' --role USER
uv run python scripts/seed_user.py admin --password 'admin' --role ADMIN
```

The example passwords are for local development only. See
[backend/README.md](backend/README.md) for database configuration, catalogue
seeding, API examples, and backend tests.

### Run the Application

Start the API from `backend/`:

```bash
./scripts/dev.sh
```

In another terminal, start the web application from `frontend/`:

```bash
npm run dev
```

Open the URL printed by Vite and sign in with a provisioned account. The API is
available at `http://127.0.0.1:8000`, its interactive documentation is at
`http://127.0.0.1:8000/docs`, and its health check is at
`http://127.0.0.1:8000/health`.

See [frontend/README.md](frontend/README.md) for frontend configuration,
development behavior, and checks.

### Run with Docker Compose

Docker Compose starts PostgreSQL, applies Alembic migrations, loads the
checked-in 100-book catalogue, then starts the API and frontend. The PostgreSQL
data is retained in the `postgres_data` named volume.

```bash
cp .env.example .env
# Replace POSTGRES_PASSWORD, DATABASE_URL, and JWT_SECRET_KEY in .env.
# DATABASE_URL must use the Compose database hostname: @db:5432.
docker compose up --build
```

Open `http://localhost:8080`. The frontend proxies API requests to the backend,
so `VITE_API_BASE_URL` is not required. The API documentation is available at
`http://localhost:8080/docs`.

The catalogue loader uses `backend/seed_books.csv`, which contains 100 rows, and
is idempotent: later `docker compose up` runs do not duplicate books. Accounts
remain explicitly provisioned, as in the local setup:

```bash
docker compose exec backend uv run --no-sync python scripts/seed_user.py alice --password 'password' --role USER
docker compose exec backend uv run --no-sync python scripts/seed_user.py admin --password 'admin' --role ADMIN
```

The example passwords are for local development only. To discard the database
volume and initialize a new database, run:

```bash
docker compose down --volumes
docker compose up --build
```

### Run Checks

Run the backend and frontend checks from the repository root:

```bash
(cd backend && ./scripts/test.sh)
(cd frontend && npm run format:check && npm run lint && npm run test && npm run build)
```

Most backend tests do not require a database. The PostgreSQL schema tests and
the loan and reservation API tests need a migrated test database supplied
through `TEST_DATABASE_URL`; see the backend guide for details.

## Assumptions and Design Decisions

- A book record represents a title, not an individually identifiable physical
  copy. Inventory is tracked using aggregate `total_copies` and
  `available_copies` values.
- A member can have at most one active loan and one active reservation for a
  title.
- Reservations can be created only when no copy is immediately available. The
  number of active reservations for a title cannot exceed its active loans, so a
  title with one loaned copy accepts one active reservation.
- A ready reservation holds one unit of title inventory until it is confirmed,
  cancelled, or expires.
- Accounts are provisioned administratively; public registration is not
  supported.
- Notifications are in-app only.
- Timestamps are stored as Unix UTC seconds and displayed using the browser's
  local time.
- Late fees are recorded against loans, but the application does not maintain a
  payable balance or collect payment.
- ISBN input is limited to ISBN-13. Formatting characters are normalized, but
  checksum validation is not performed.

## Out of Scope and Potential Improvements

- Individually tracked physical copies, barcodes, and copy condition
- Late-fee balances, waivers, payment methods, and payment processing
- Loan renewals
- Public registration, editable profiles, reading interests, and recommendations
- Email, SMS, and push notifications
- A general multi-member wait-list with FIFO fulfilment
- Wait-list position estimates and administrative reservation queue management
- A distributed scheduler or lease for reservation expiry in multi-process
  deployments

## Documentation

- [Backend guide](backend/README.md)
- [Frontend guide](frontend/README.md)
- [Developer guide](docs/DEVELOPER_GUIDE.md)
- [OpenAPI specification](docs/openapi.json)
