"""SQLAlchemy-backed database for ChopTheBill.

Database-agnostic: all SQL goes through SQLAlchemy ORM models below, so the
same code works for SQLite (default) and future databases (e.g. Postgres)
just by pointing ``DATABASE_URL`` at a different server.

Config:
    DATABASE_URL — SQLAlchemy URL. Defaults to ``sqlite:///./chopthebill.db``.
    Examples:
        sqlite:///./chopthebill.db
        sqlite:////tmp/test.db
        postgresql+psycopg2://user:pass@localhost:5432/chopthebill

Public functions keep the same dict-based interface as the old in-memory
store, so route code (``app.main``) is unchanged.
"""
from __future__ import annotations

import os
import secrets
from datetime import date as date_type
from typing import Iterator

from sqlalchemy import (
    Date,
    Float,
    ForeignKey,
    String,
    create_engine,
    select,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool


def _database_url() -> str:
    return os.environ.get("DATABASE_URL", "sqlite:///./chopthebill.db")


def _create_engine(url: str):
    """Create an engine with sensible per-dialect defaults (DB-agnostic)."""
    kwargs: dict = {}
    if url.startswith("sqlite:"):
        # Needed for FastAPI's threaded server + tests sharing one engine.
        kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in url:
            # In-memory SQLite is per-connection — share one via StaticPool.
            kwargs["poolclass"] = StaticPool
    return create_engine(url, **kwargs)


engine = _create_engine(_database_url())
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, default="")


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class GroupMember(Base):
    __tablename__ = "group_members"

    group_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    group_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    payer_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"), nullable=False)
    day: Mapped[date_type] = mapped_column(Date, nullable=False)


class Split(Base):
    __tablename__ = "splits"

    expense_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("expenses.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"), primary_key=True)
    share_amount: Mapped[float] = mapped_column(Float, nullable=False)


Base.metadata.create_all(engine)


def configure(database_url: str) -> None:
    """Point the store at a different DB (e.g. tests, Postgres). Rebuilds tables."""
    global engine, SessionLocal
    engine = _create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)


def reset() -> None:
    """Drop + recreate all tables (test isolation). Works on any backend."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def _session() -> Iterator[Session]:
    return SessionLocal()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(4)}"


def _norm_email(email: str) -> str:
    return email.strip().lower()


def _user_to_record(u: User) -> dict:
    return {"id": u.id, "name": u.name, "email": u.email, "password_hash": u.password_hash}


# --- users ---------------------------------------------------------------

def create_user(name: str, email: str, password_hash: str) -> dict:
    email = _norm_email(email)
    with _session() as s:
        user = User(id=_new_id("u"), name=name.strip(), email=email, password_hash=password_hash)
        s.add(user)
        s.commit()
        s.refresh(user)
        return _user_to_record(user)


def create_placeholder_user(email: str) -> dict:
    """Create a member stub for an unknown email (matches mockApi behavior)."""
    return create_user(name=email.strip(), email=email, password_hash="")


def find_user_by_email(email: str) -> dict | None:
    with _session() as s:
        user = s.scalar(select(User).where(User.email == _norm_email(email)))
        return _user_to_record(user) if user else None


def get_user(user_id: str) -> dict | None:
    with _session() as s:
        user = s.get(User, user_id)
        return _user_to_record(user) if user else None


def get_user_record_by_email(email: str) -> dict | None:
    """Internal record (incl. password_hash). Used by tests; never serialized."""
    return find_user_by_email(email)


def list_user_records() -> list[dict]:
    with _session() as s:
        return [_user_to_record(u) for u in s.scalars(select(User)).all()]


def public_user(record: dict) -> dict:
    return {"id": record["id"], "name": record["name"], "email": record["email"]}


# --- groups --------------------------------------------------------------

def _member_ids(s: Session, group_id: str) -> list[str]:
    return list(
        s.scalars(select(GroupMember.user_id).where(GroupMember.group_id == group_id)).all()
    )


def create_group(name: str, member_ids: list[str]) -> dict:
    with _session() as s:
        group = Group(id=_new_id("g"), name=name.strip())
        s.add(group)
        for uid in member_ids:
            s.add(GroupMember(group_id=group.id, user_id=uid))
        s.commit()
        return {"id": group.id, "name": group.name, "members": list(member_ids)}


def get_group(group_id: str) -> dict | None:
    with _session() as s:
        group = s.get(Group, group_id)
        if group is None:
            return None
        return {"id": group.id, "name": group.name, "members": _member_ids(s, group.id)}


def list_groups_for_user(user_id: str) -> list[dict]:
    with _session() as s:
        group_ids = list(
            s.scalars(select(GroupMember.group_id).where(GroupMember.user_id == user_id)).all()
        )
        out = []
        for gid in group_ids:
            group = s.get(Group, gid)
            if group is not None:
                out.append({"id": group.id, "name": group.name, "members": _member_ids(s, gid)})
        return out


# --- expenses ------------------------------------------------------------

def _expense_to_dict(s: Session, e: Expense) -> dict:
    splits = [
        {"user_id": sp.user_id, "share_amount": float(sp.share_amount)}
        for sp in s.scalars(select(Split).where(Split.expense_id == e.id)).all()
    ]
    return {
        "id": e.id,
        "group_id": e.group_id,
        "description": e.description,
        "amount": float(e.amount),
        "payer_id": e.payer_id,
        "date": e.day.isoformat(),
        "splits": splits,
    }


def create_expense(
    group_id: str,
    description: str,
    amount: float,
    payer_id: str,
    splits: list[dict],
    day: str,
) -> dict:
    parsed = date_type.fromisoformat(day) if isinstance(day, str) else day
    with _session() as s:
        expense = Expense(
            id=_new_id("e"),
            group_id=group_id,
            description=description.strip(),
            amount=float(amount),
            payer_id=payer_id,
            day=parsed,
        )
        s.add(expense)
        for sp in splits:
            s.add(
                Split(
                    expense_id=expense.id,
                    user_id=sp["user_id"],
                    share_amount=float(sp["share_amount"]),
                )
            )
        s.commit()
        return _expense_to_dict(s, expense)


def list_expenses(group_id: str) -> list[dict]:
    with _session() as s:
        expenses = s.scalars(select(Expense).where(Expense.group_id == group_id)).all()
        return [_expense_to_dict(s, e) for e in expenses]
