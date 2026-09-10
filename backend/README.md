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
uv run fastapi dev main.py
```

The API is available at `http://127.0.0.1:8000`, with interactive documentation at `/docs` and a health check at `/health`.

## Configuration

`DATABASE_URL` must be a PostgreSQL SQLAlchemy URL, for example
`postgresql+psycopg://library_app:password@localhost:5432/library_db`.
`JWT_SECRET_KEY` must be a cryptographically random signing secret. Both values
are required. `.env` is local-only and must not be committed; use `.env.example`
as the safe template.

## Provision an account

Accounts are provisioned locally with the non-public seed helper, not through an
API route:

```bash
uv run python scripts/seed_user.py alice --password 'password' --role USER
uv run python scripts/seed_user.py admin --password 'admin' --role ADMIN
```

The helper rejects duplicate usernames and stores only an Argon2id password hash.

## Login

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"password"}'
```

Successful responses contain a one-hour HS256 bearer access token. Invalid
usernames and passwords return the same `401 Invalid username or password`
response.
