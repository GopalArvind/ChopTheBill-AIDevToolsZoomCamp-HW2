"""ChopTheBill FastAPI backend — routes per openapi.yaml."""
from __future__ import annotations

from datetime import date

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import auth, db
from .balances import compute_balances
from .schemas import (
    AuthResponse,
    BalanceResponse,
    CreateExpenseRequest,
    CreateGroupRequest,
    Expense,
    Group,
    LoginRequest,
    SignupRequest,
    User,
)

app = FastAPI(title="ChopTheBill")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bearer = HTTPBearer(auto_error=False)


def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        user_id = auth.decode_token(creds.credentials)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token") from None
    user = db.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


def require_member(group_id: str, user: dict) -> dict:
    group = db.get_group(group_id)
    if group is None or user["id"] not in group["members"]:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


# --- auth -----------------------------------------------------------------

@app.post("/signup", response_model=AuthResponse)
def signup(body: SignupRequest) -> dict:
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name required")
    if db.find_user_by_email(body.email) is not None:
        raise HTTPException(status_code=400, detail="Email already registered")
    record = db.create_user(name=name, email=body.email, password_hash=auth.hash_password(body.password))
    return {"user": db.public_user(record), "token": auth.create_token(record["id"])}


@app.post("/login", response_model=AuthResponse)
def login(body: LoginRequest) -> dict:
    record = db.find_user_by_email(body.email)
    if record is None or not auth.verify_password(body.password, record["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"user": db.public_user(record), "token": auth.create_token(record["id"])}


@app.get("/me", response_model=User)
def get_profile(user: dict = Depends(current_user)) -> dict:
    return db.public_user(user)


# --- groups ---------------------------------------------------------------

@app.get("/groups", response_model=list[Group])
def list_groups(user: dict = Depends(current_user)) -> list[dict]:
    return db.list_groups_for_user(user["id"])


@app.post("/groups", response_model=Group)
def create_group(body: CreateGroupRequest, user: dict = Depends(current_user)) -> dict:
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Group name required")
    member_ids: list[str] = [user["id"]]
    for raw in body.members or []:
        email = raw.strip()
        if not email or "@" not in email:
            continue
        existing = db.find_user_by_email(email)
        if existing is not None:
            uid = existing["id"]
        else:
            uid = db.create_placeholder_user(email)["id"]
        if uid not in member_ids:
            member_ids.append(uid)
    return db.create_group(name=body.name.strip(), member_ids=member_ids)


# --- expenses --------------------------------------------------------------

@app.get("/expenses/{group_id}", response_model=list[Expense])
def list_expenses(group_id: str, user: dict = Depends(current_user)) -> list[dict]:
    require_member(group_id, user)
    return db.list_expenses(group_id)


@app.post("/expenses/{group_id}", response_model=Expense)
def create_expense(group_id: str, body: CreateExpenseRequest, user: dict = Depends(current_user)) -> dict:
    group = require_member(group_id, user)
    if not body.description.strip():
        raise HTTPException(status_code=400, detail="Description required")

    payer_id = body.payer_id or user["id"]
    if payer_id not in group["members"]:
        raise HTTPException(status_code=400, detail="Payer must be a group member")

    if not body.splits:
        share = round(float(body.amount) / len(group["members"]), 2)
        splits = [{"user_id": uid, "share_amount": share} for uid in group["members"]]
    else:
        splits = [{"user_id": s.user_id, "share_amount": float(s.share_amount)} for s in body.splits]
        for s in splits:
            if s["user_id"] not in group["members"]:
                raise HTTPException(status_code=400, detail="Split user must be a group member")
        total = sum(s["share_amount"] for s in splits)
        if abs(total - float(body.amount)) > 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"Custom shares must sum to {float(body.amount):.2f} (now {total:.2f})",
            )

    return db.create_expense(
        group_id=group_id,
        description=body.description.strip(),
        amount=float(body.amount),
        payer_id=payer_id,
        splits=splits,
        day=(body.date or date.today()).isoformat(),
    )


# --- balances ---------------------------------------------------------------

@app.get("/balances/{group_id}", response_model=BalanceResponse)
def get_balances(group_id: str, user: dict = Depends(current_user)) -> dict:
    require_member(group_id, user)
    return compute_balances(db.list_expenses(group_id))


# --- users ------------------------------------------------------------------

@app.get("/users", response_model=list[User])
def list_users(user: dict = Depends(current_user)) -> list[dict]:
    _ = user  # auth required; full list needed by GroupPage userMap
    return [db.public_user(r) for r in db.list_user_records()]
