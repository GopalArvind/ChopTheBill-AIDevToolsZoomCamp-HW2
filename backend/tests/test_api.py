"""Endpoint tests for the ChopTheBill FastAPI backend.

Contract source: /openapi.yaml (derived from frontend/src/services/realApi.js).
Uses the mock in-memory DB (app.db) with a reset fixture so tests are isolated.

TDD: these were written before the implementation.
"""
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app


@pytest.fixture(autouse=True)
def _reset_store():
    db.reset()
    yield
    db.reset()


@pytest.fixture()
def client():
    return TestClient(app)


def signup(client, name="Demo User", email="demo@example.com", password="demo1234"):
    r = client.post("/signup", json={"name": name, "email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()


def login(client, email="demo@example.com", password="demo1234"):
    r = client.post("/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()


def auth(token):
    return {"Authorization": f"Bearer {token}"}


# --- auth -----------------------------------------------------------------

def test_signup_returns_user_and_token(client):
    data = signup(client)
    assert set(data["user"]) == {"id", "name", "email"}
    assert data["user"]["name"] == "Demo User"
    assert data["user"]["email"] == "demo@example.com"
    assert data["token"]


def test_signup_duplicate_email_is_400(client):
    signup(client)
    r = client.post("/signup", json={"name": "X", "email": "demo@example.com", "password": "other123"})
    assert r.status_code == 400
    assert "already registered" in r.json()["detail"].lower()


def test_password_is_hashed_not_stored_plain(client):
    signup(client, password="supersecret1")
    record = db.get_user_record_by_email("demo@example.com")
    assert record is not None
    assert record["password_hash"] != "supersecret1"
    assert "password" not in record or record.get("password") != "supersecret1"


def test_login_ok_and_me_roundtrip(client):
    signed = signup(client)
    data = login(client)
    assert data["user"]["id"] == signed["user"]["id"]

    me = client.get("/me", headers=auth(data["token"]))
    assert me.status_code == 200, me.text
    assert me.json() == signed["user"]


def test_login_invalid_password_is_401(client):
    signup(client)
    r = client.post("/login", json={"email": "demo@example.com", "password": "wrong"})
    assert r.status_code == 401


def test_protected_endpoints_require_auth(client):
    # No token at all -> 401 everywhere (not FastAPI's default 403).
    assert client.get("/me").status_code == 401
    assert client.get("/groups").status_code == 401
    assert client.post("/groups", json={"name": "G"}).status_code == 401
    assert client.get("/expenses/g_x").status_code == 401
    assert client.post("/expenses/g_x", json={"description": "D", "amount": 10}).status_code == 401
    assert client.get("/balances/g_x").status_code == 401
    assert client.get("/users").status_code == 401
    # Garbage token -> 401 as well.
    bad = auth("garbage.token.here")
    assert client.get("/me", headers=bad).status_code == 401
    assert client.get("/groups", headers=bad).status_code == 401


# --- groups ---------------------------------------------------------------

def test_create_and_list_groups(client):
    token = signup(client)["token"]
    created = client.post("/groups", json={"name": "Weekend Trip", "members": []}, headers=auth(token))
    assert created.status_code == 200, created.text
    group = created.json()
    assert group["name"] == "Weekend Trip"
    assert len(group["members"]) == 1  # creator auto-added

    listed = client.get("/groups", headers=auth(token))
    assert listed.status_code == 200
    assert [g["id"] for g in listed.json()] == [group["id"]]


def test_create_group_resolves_member_emails(client):
    bob = signup(client, name="Bob", email="bob@example.com")
    alice_token = signup(client, name="Alice", email="alice@example.com")["token"]
    r = client.post(
        "/groups",
        json={"name": "Trip", "members": ["bob@example.com"]},
        headers=auth(alice_token),
    )
    assert r.status_code == 200, r.text
    members = r.json()["members"]
    assert bob["user"]["id"] in members
    assert len(members) == 2  # alice + bob


def test_create_group_unknown_email_creates_placeholder_user(client):
    token = signup(client)["token"]
    r = client.post(
        "/groups", json={"name": "Trip", "members": ["ghost@example.com"]}, headers=auth(token)
    )
    assert r.status_code == 200, r.text
    assert len(r.json()["members"]) == 2

    users = client.get("/users", headers=auth(token)).json()
    assert "ghost@example.com" in [u["email"] for u in users]


def test_create_group_name_required(client):
    token = signup(client)["token"]
    r = client.post("/groups", json={"name": "   ", "members": []}, headers=auth(token))
    assert r.status_code == 400


def test_groups_are_scoped_to_member(client):
    alice_token = signup(client, name="Alice", email="alice@example.com")["token"]
    bob_token = signup(client, name="Bob", email="bob@example.com")["token"]
    client.post("/groups", json={"name": "A-only", "members": []}, headers=auth(alice_token))
    assert client.get("/groups", headers=auth(bob_token)).json() == []


# --- expenses -------------------------------------------------------------

def _make_group(client, token, name="Trip", members=()):
    r = client.post("/groups", json={"name": name, "members": list(members)}, headers=auth(token))
    assert r.status_code == 200, r.text
    return r.json()


def test_create_expense_defaults_to_equal_split_and_today(client):
    alice = signup(client, name="Alice", email="alice@example.com")
    bob = signup(client, name="Bob", email="bob@example.com")
    token = alice["token"]
    group = _make_group(client, token, members=["bob@example.com"])

    r = client.post(
        f"/expenses/{group['id']}",
        json={"description": "Dinner", "amount": 90, "payer_id": alice["user"]["id"], "splits": None},
        headers=auth(token),
    )
    assert r.status_code == 200, r.text
    expense = r.json()
    assert expense["group_id"] == group["id"]
    assert expense["date"] == date.today().isoformat()
    by_user = {s["user_id"]: s["share_amount"] for s in expense["splits"]}
    assert by_user == {alice["user"]["id"]: 45.0, bob["user"]["id"]: 45.0}

    listed = client.get(f"/expenses/{group['id']}", headers=auth(token))
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_create_expense_defaults_payer_to_current_user(client):
    alice = signup(client, name="Alice", email="alice@example.com")
    group = _make_group(client, alice["token"])
    r = client.post(
        f"/expenses/{group['id']}",
        json={"description": "Taxi", "amount": 20},
        headers=auth(alice["token"]),
    )
    assert r.status_code == 200, r.text
    assert r.json()["payer_id"] == alice["user"]["id"]


def test_create_expense_custom_splits(client):
    alice = signup(client, name="Alice", email="alice@example.com")
    bob = signup(client, name="Bob", email="bob@example.com")
    token = alice["token"]
    group = _make_group(client, token, members=["bob@example.com"])
    payload = {
        "description": "Dinner",
        "amount": 100,
        "payer_id": alice["user"]["id"],
        "splits": [
            {"user_id": alice["user"]["id"], "share_amount": 70},
            {"user_id": bob["user"]["id"], "share_amount": 30},
        ],
    }
    r = client.post(f"/expenses/{group['id']}", json=payload, headers=auth(token))
    assert r.status_code == 200, r.text
    assert r.json()["splits"] == payload["splits"]


def test_create_expense_validations(client):
    alice = signup(client, name="Alice", email="alice@example.com")
    token = alice["token"]
    group = _make_group(client, token)

    # amount must be > 0 (pydantic -> 422)
    r = client.post(
        f"/expenses/{group['id']}", json={"description": "D", "amount": 0}, headers=auth(token)
    )
    assert r.status_code == 422

    # description required
    r = client.post(
        f"/expenses/{group['id']}", json={"description": "  ", "amount": 10}, headers=auth(token)
    )
    assert r.status_code == 400

    # custom splits must sum to amount (±0.01)
    r = client.post(
        f"/expenses/{group['id']}",
        json={
            "description": "D",
            "amount": 100,
            "splits": [{"user_id": alice["user"]["id"], "share_amount": 60}],
        },
        headers=auth(token),
    )
    assert r.status_code == 400

    # payer must be a group member
    r = client.post(
        f"/expenses/{group['id']}",
        json={"description": "D", "amount": 10, "payer_id": "u_stranger"},
        headers=auth(token),
    )
    assert r.status_code == 400

    # unknown group
    r = client.post("/expenses/g_nope", json={"description": "D", "amount": 10}, headers=auth(token))
    assert r.status_code == 404


def test_non_members_cannot_see_or_add_expenses(client):
    alice_token = signup(client, name="Alice", email="alice@example.com")["token"]
    bob_token = signup(client, name="Bob", email="bob@example.com")["token"]
    group = _make_group(client, alice_token)

    assert client.get(f"/expenses/{group['id']}", headers=auth(bob_token)).status_code == 404
    assert client.get(f"/balances/{group['id']}", headers=auth(bob_token)).status_code == 404
    r = client.post(
        f"/expenses/{group['id']}",
        json={"description": "Sneaky", "amount": 10},
        headers=auth(bob_token),
    )
    assert r.status_code == 404


# --- balances -------------------------------------------------------------

def test_balances_minimized_transactions(client):
    alice = signup(client, name="Alice", email="alice@example.com")
    bob = signup(client, name="Bob", email="bob@example.com")
    carol = signup(client, name="Carol", email="carol@example.com")
    token = alice["token"]
    group = _make_group(client, token, members=["bob@example.com", "carol@example.com"])

    # Alice pays 90 split equally: bob and carol each owe alice 30.
    r = client.post(
        f"/expenses/{group['id']}",
        json={
            "description": "Dinner",
            "amount": 90,
            "payer_id": alice["user"]["id"],
            "splits": [
                {"user_id": alice["user"]["id"], "share_amount": 30},
                {"user_id": bob["user"]["id"], "share_amount": 30},
                {"user_id": carol["user"]["id"], "share_amount": 30},
            ],
        },
        headers=auth(token),
    )
    assert r.status_code == 200, r.text

    bal = client.get(f"/balances/{group['id']}", headers=auth(token))
    assert bal.status_code == 200, bal.text
    body = bal.json()
    assert body["net"][alice["user"]["id"]] == pytest.approx(60.0)
    assert body["net"][bob["user"]["id"]] == pytest.approx(-30.0)
    assert body["net"][carol["user"]["id"]] == pytest.approx(-30.0)
    assert sorted(t["amount"] for t in body["transactions"]) == [30.0, 30.0]
    assert {t["to_user_id"] for t in body["transactions"]} == {alice["user"]["id"]}


def test_balances_empty_group_settles_cleanly(client):
    token = signup(client)["token"]
    group = _make_group(client, token)
    bal = client.get(f"/balances/{group['id']}", headers=auth(token))
    assert bal.status_code == 200
    assert bal.json() == {"net": {}, "transactions": []}


# --- users ----------------------------------------------------------------

def test_list_users_returns_public_fields_only(client):
    token = signup(client)["token"]
    r = client.get("/users", headers=auth(token))
    assert r.status_code == 200, r.text
    users = r.json()
    assert len(users) == 1
    assert set(users[0]) == {"id", "name", "email"}
