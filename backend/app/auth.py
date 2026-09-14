"""Password hashing (bcrypt) + JWT (HS256) auth helpers."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

SECRET_KEY = os.environ.get("CHOPTHEBIL_SECRET", "dev-only-secret-change-me-please-32")
ALGORITHM = "HS256"
EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": user_id, "iat": now, "exp": now + timedelta(days=EXPIRE_DAYS)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> str:
    """Return the user id (sub) or raise ValueError on any problem."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError as e:
        raise ValueError(f"Invalid token: {e}") from e
    sub = payload.get("sub")
    if not sub:
        raise ValueError("Invalid token: missing sub")
    return sub
