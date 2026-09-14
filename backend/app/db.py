"""Mock in-memory database for ChopTheBill.

Swappable later: all access goes through the functions below, so a real
(SQLAlchemy/SQLite/Postgres) implementation can replace this module without
touching route code. Mirror of frontend/src/services/mockApi.js semantics.
"""
from __future__ import annotations

import secrets

_users: dict[str, dict] = {}  # id -> {id, name, email, password_hash}
_users_by_email: dict[str, str] = {}  # normalized email -> id
_groups: dict[str, dict] = {}  # id -> {id, name, members: [user_id]}
_expenses: dict[str, dict] = {}  # id -> expense record


def reset() -> None:
    _users.clear()
    _users_by_email.clear()
    _groups.clear()
    _expenses.clear()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(4)}"


def _norm_email(email: str) -> str:
    return email.strip().lower()


# --- users ---------------------------------------------------------------

def create_user(name: str, email: str, password_hash: str) -> dict:
    email = _norm_email(email)
    user = {"id": _new_id("u"), "name": name.strip(), "email": email, "password_hash": password_hash}
    _users[user["id"]] = user
    _users_by_email[email] = user["id"]
    return user


def create_placeholder_user(email: str) -> dict:
    """Create a member stub for an unknown email (matches mockApi behavior)."""
    return create_user(name=email.strip(), email=email, password_hash="")


def find_user_by_email(email: str) -> dict | None:
    uid = _users_by_email.get(_norm_email(email))
    return _users.get(uid) if uid else None


def get_user(user_id: str) -> dict | None:
    return _users.get(user_id)


def get_user_record_by_email(email: str) -> dict | None:
    """Internal record (incl. password_hash). Used by tests; never serialized."""
    return find_user_by_email(email)


def list_user_records() -> list[dict]:
    return list(_users.values())


def public_user(record: dict) -> dict:
    return {"id": record["id"], "name": record["name"], "email": record["email"]}


# --- groups --------------------------------------------------------------

def create_group(name: str, member_ids: list[str]) -> dict:
    group = {"id": _new_id("g"), "name": name.strip(), "members": list(member_ids)}
    _groups[group["id"]] = group
    return group


def get_group(group_id: str) -> dict | None:
    return _groups.get(group_id)


def list_groups_for_user(user_id: str) -> list[dict]:
    return [g for g in _groups.values() if user_id in g["members"]]


# --- expenses ------------------------------------------------------------

def create_expense(
    group_id: str,
    description: str,
    amount: float,
    payer_id: str,
    splits: list[dict],
    day: str,
) -> dict:
    expense = {
        "id": _new_id("e"),
        "group_id": group_id,
        "description": description.strip(),
        "amount": float(amount),
        "payer_id": payer_id,
        "date": day,
        "splits": [{"user_id": s["user_id"], "share_amount": float(s["share_amount"])} for s in splits],
    }
    _expenses[expense["id"]] = expense
    return expense


def list_expenses(group_id: str) -> list[dict]:
    return [e for e in _expenses.values() if e["group_id"] == group_id]
