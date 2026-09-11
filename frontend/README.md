# Library Frontend

The React frontend provides sign-in and a protected book catalogue for members
and administrators.

## Requirements

- Node.js 22.12 or later
- npm
- A running library backend

## Run Locally

Start the backend by following [backend/README.md](../backend/README.md),
including its database migration and account provisioning steps. Then run:

```bash
npm install
npm run dev
```

The Vite development server proxies `/auth`, `/books`, `/loans`,
`/reservations`, and `/notifications` to `http://127.0.0.1:8000`. Sign in with a
provisioned account, such as `alice` after running the backend seed command.

## Configuration

For a separately hosted API, copy `.env.example` to `.env` and set the public
`VITE_API_BASE_URL`:

```bash
cp .env.example .env
```

This value is bundled into the browser application and must not contain a
secret. Leave it blank to use the development proxy.

## Application Behavior

Administrators can browse, view, add, edit, and delete books. Members can browse
and view books, borrow available titles, review active and returned loans,
return their own active loans, and manage reservations and notifications.

The catalogue supports title and author search, inclusive publication-date
filters, and sorting by relevance, title, author, or publication date. Date
filters are interpreted as UTC calendar-day bounds. Loan and reservation dates
are displayed using the browser's local time.

Late fees displayed in member history are authoritative values returned by the
server. The frontend does not calculate fees, maintain balances, or collect
payments.

## Checks

Run from `frontend/`:

```bash
npm run format:check
npm run lint
npm run test
npm run build
```
