"""Pydantic schemas mirroring openapi.yaml components."""
from __future__ import annotations

from datetime import date as date_type

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=1)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class User(BaseModel):
    id: str
    name: str
    email: str


class AuthResponse(BaseModel):
    user: User
    token: str


class CreateGroupRequest(BaseModel):
    name: str = Field(min_length=1)
    members: list[str] = []


class Group(BaseModel):
    id: str
    name: str
    members: list[str]


class Split(BaseModel):
    user_id: str
    share_amount: float = Field(ge=0)


class CreateExpenseRequest(BaseModel):
    description: str = Field(min_length=1)
    amount: float = Field(gt=0)
    payer_id: str | None = None
    splits: list[Split] | None = None
    date: date_type | None = None


class Expense(BaseModel):
    id: str
    group_id: str
    description: str
    amount: float
    payer_id: str
    date: date_type
    splits: list[Split]


class Transaction(BaseModel):
    from_user_id: str
    to_user_id: str
    amount: float


class BalanceResponse(BaseModel):
    net: dict[str, float]
    transactions: list[Transaction]
