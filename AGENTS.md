# AGENTS.md — ChopTheBill

## Project Overview
ChopTheBill is a web app for tracking shared group expenses. MVP scope is balance tracking only — no payment integration. See `specs.md` (source of truth) and `README.md`.

## Tech Stack
- Frontend: React
- Backend: FastAPI
- Database: SQLite (design to allow future Postgres/MySQL migration)
- Auth: JWT Bearer tokens, password hashing

## Planned Structure
- `/frontend` — React app (Login/Signup, Dashboard, Group page, Navbar)
- `/backend` — FastAPI app (`/signup`, `/login`, `/groups`, `/expenses/{group_id}`, `/balances/{group_id}`)
- Data models: User, Group, Expense, Split — see `specs.md`

## Agent Guidelines
1. Follow `specs.md` for data model, routes, and user flow. Don't add non-MVP features (categories, export, notifications, multi-currency, admin controls) unless asked.
2. Backend: use FastAPI + Pydantic validation, hashed passwords, JWT auth on all group/expense/balance routes. Support groups up to ~50 members.
3. Frontend: simple, intuitive UI — expense table (description, payer, amount, date), Add Expense modal, balance summary (who owes whom).
4. Balance logic: compute net balances and minimize transactions.
5. Keep changes small, prefer editing existing files, and verify with tests/run before finishing.

## Security / Constraints
- Never commit secrets, tokens, or password hashes.
- Validate all inputs server-side; check group membership before exposing expenses/balances.
