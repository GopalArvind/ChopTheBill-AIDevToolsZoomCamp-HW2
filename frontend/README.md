# ChopTheBill Frontend

React app per `_docs/specs.md`. All backend calls are centralized in `src/services/api.js`.

- `VITE_USE_MOCK=true` (default): uses `src/services/mockApi.js` — full app runs without a backend, seeded with a demo user (`demo@example.com` / `demo1234`).
- `VITE_USE_MOCK=false`: uses `src/services/realApi.js` against `VITE_API_URL` (FastAPI).

## Run

```bash
cd frontend
npm install
npm run dev
```

## Structure

- `src/services/api.js` — single entry point for signup, login, groups, expenses, balances
- `src/services/mockApi.js` / `realApi.js` — mock + real implementations (same interface)
- `src/services/balance.js` — net balances + minimized transactions
- `src/pages/` — Login, Signup, Dashboard, GroupPage
- `src/components/` — Navbar, AddExpenseModal, BalanceSummary
