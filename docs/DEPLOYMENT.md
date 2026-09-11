# Deployment Guide

Deploy the frontend to Vercel, the FastAPI backend to Render, and PostgreSQL to
Supabase. Do not commit database URLs, passwords, or JWT secrets.

## 1. Prepare Supabase

Create a Supabase project, then use its direct connection URL to initialize the
application schema and data. Replace the URL prefix with `postgresql+psycopg`
because the backend uses Psycopg 3 through SQLAlchemy. URL-encode special
characters in the password.

```bash
cd backend

export DATABASE_URL='postgresql+psycopg://postgres:<encoded-password>@db.<project-ref>.supabase.co:5432/postgres?sslmode=require'
export JWT_SECRET_KEY="$(openssl rand -hex 32)"

uv sync
uv run alembic upgrade head
uv run python scripts/seed_books.py --load
uv run python scripts/seed_user.py admin --password '<strong-password>' --role ADMIN
```

Save the generated `JWT_SECRET_KEY`; Render must use the same value. Use a
Supabase Direct connection for Alembic migrations. If the deployment host
cannot reach that endpoint, use Supabase's Session Pooler URL instead, retaining
the `postgresql+psycopg://` prefix.

## 2. Deploy the Backend to Render

Create a Render Web Service from this repository:

- Runtime: Docker
- Root Directory: `backend`
- Dockerfile: `backend/Dockerfile`
- Health Check Path: `/health`
- Branch: the branch to deploy, usually `main`

Render environment variables:

```env
DATABASE_URL=postgresql+psycopg://postgres:<encoded-password>@db.<project-ref>.supabase.co:5432/postgres?sslmode=require
JWT_SECRET_KEY=<the-secret-generated-during-Supabase-setup>
CORS_ALLOWED_ORIGINS=https://<your-vercel-project>.vercel.app
```

`DATABASE_URL` takes precedence over `POSTGRES_DB`, `POSTGRES_USER`, and
`POSTGRES_PASSWORD`, so do not set those variables on Render. Render supplies
`PORT`; the backend Docker image binds FastAPI to it automatically.

After Render deploys, verify the service and note its public URL:

```bash
curl https://<your-render-service>.onrender.com/health
```

The expected response is:

```json
{"status":"ok"}
```

## 3. Deploy the Frontend to Vercel

Create a Vercel project from this repository:

- Root Directory: `frontend`
- Framework: Vite
- Build Command: `npm run build`
- Output Directory: `dist`

Set this Vercel Production environment variable, then redeploy:

```env
VITE_API_BASE_URL=https://<your-render-service>.onrender.com
```

Do not include a trailing slash. `VITE_*` variables are embedded in the browser
bundle, so they must never contain secrets.

After Vercel assigns the production URL, set that exact origin in Render's
`CORS_ALLOWED_ORIGINS` and redeploy the backend. For example:

```env
CORS_ALLOWED_ORIGINS=https://library-app.vercel.app
```

For multiple permitted browser origins, provide a comma-separated list with no
trailing slash:

```env
CORS_ALLOWED_ORIGINS=https://library-app.vercel.app,https://staging-library-app.vercel.app
```

## Operational Notes

- Run `uv run alembic upgrade head` after adding a migration, before deploying
  backend code that requires it.
- Keep the backend at one instance initially. The reservation-expiry worker runs
  inside every backend process.
- Render free services can sleep, so reservation expiry is not prompt while the
  service is inactive. Reservation mutations still expire relevant holds.
- Rotate a compromised `JWT_SECRET_KEY` deliberately: existing bearer tokens
  become invalid immediately.
