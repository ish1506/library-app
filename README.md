# Library App

## Frontend

The React frontend provides the library sign-in screen. It requires Node.js 20.19 or later and npm.

Start the backend first by following [backend/README.md](backend/README.md), including the database migration and account provisioning steps. Then, from `frontend/`:

```bash
npm install
npm run dev
```

The Vite dev server proxies requests to `/auth` to the backend at `http://127.0.0.1:8000`, avoiding a local CORS request. Sign in with a provisioned account, for example `alice` after running the seed command in the backend README.

For a separately hosted API, copy `.env.example` to `.env` in `frontend/` and set the public `VITE_API_BASE_URL`. This value is bundled into the browser application, so it must never contain a secret.

Run frontend checks from `frontend/`:

```bash
npm run lint
npm run test
npm run build
```
