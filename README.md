# Library App

## Frontend

The React frontend provides sign-in and a protected Books catalogue. It requires Node.js 20.19 or later and npm.

Start the backend first by following [backend/README.md](backend/README.md), including the database migration and account provisioning steps. Then, from `frontend/`:

```bash
npm install
npm run dev
```

The Vite dev server proxies requests to `/auth`, `/books`, and `/loans` to the backend at `http://127.0.0.1:8000`, avoiding a local CORS request. Sign in with a provisioned account, for example `alice` after running the seed command in the backend README.

Administrators can browse, view, add, edit, and delete books. Normal users can browse and view books, borrow available titles, review active and returned loan history, return their own active loans, and manage reservations. Loan dates are displayed using the browser's local date and time. The member history displays server-authoritative incurred late fees in USD; it does not collect payments or calculate balances. Reservation timing is configured in `backend/config/library.yaml`; renewals and copy-level workflows are not included.

The catalogue supports searching title and author text, filtering by publication date, and sorting by relevance (the default), title, author, or publication date in ascending or descending order. Enter filters and choose **Apply filters** to load results; **Clear filters** returns to the full catalogue and default ordering. Date bounds are inclusive calendar days interpreted in UTC, so the start date begins at `00:00:00Z` and the end date ends at `23:59:59Z`. Sorting is performed by the backend and is retained when retrying, viewing details, or refreshing after administrator changes.

For a separately hosted API, copy `.env.example` to `.env` in `frontend/` and set the public `VITE_API_BASE_URL`. This value is bundled into the browser application, so it must never contain a secret.

Run frontend checks from `frontend/`:

```bash
npm run lint
npm run test
npm run build
```
