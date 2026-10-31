from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models import User
from backend.rate_limit import auth_rate_limit
from backend.security import (
    create_token_pair,
    hash_password,
    validate_refresh_session,
    verify_password,
)
from backend.serializers import user_json


router = APIRouter(prefix="/auth", tags=["auth"])
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class RegisterBody(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=8, max_length=128)
    fullName: str = Field(min_length=2, max_length=120)


class LoginBody(BaseModel):
    email: str
    password: str


class RefreshBody(BaseModel):
    refreshToken: str


def auth_payload(db: Session, user: User, *, commit: bool = True) -> dict:
    access, refresh = create_token_pair(db, user, commit=commit)
    return {"accessToken": access, "refreshToken": refresh, "user": user_json(user)}


@router.post("/register", status_code=201, dependencies=[Depends(auth_rate_limit)])
def register(body: RegisterBody, db: Session = Depends(get_db)) -> dict:
    email = body.email.strip().casefold()
    if not EMAIL_PATTERN.match(email):
        raise HTTPException(status_code=422, detail="Email không hợp lệ.")
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email đã được sử dụng.")
    full_name = body.fullName.strip()
    if len(full_name) < 2:
        raise HTTPException(status_code=422, detail="Họ và tên phải có ít nhất 2 ký tự.")
    user = User(
        email=email,
        full_name=full_name,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email đã được sử dụng.") from exc
    db.refresh(user)
    return auth_payload(db, user)


@router.post("/login", dependencies=[Depends(auth_rate_limit)])
def login(body: LoginBody, db: Session = Depends(get_db)) -> dict:
    user = db.scalar(select(User).where(User.email == body.email.strip().casefold()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng.")
    return auth_payload(db, user)


@router.post("/refresh", dependencies=[Depends(auth_rate_limit)])
def refresh(body: RefreshBody, db: Session = Depends(get_db)) -> dict:
    session, user = validate_refresh_session(db, body.refreshToken)
    session.revoked = True
    payload = auth_payload(db, user, commit=False)
    db.commit()
    return payload


@router.post("/logout", status_code=204)
def logout(body: RefreshBody, db: Session = Depends(get_db)) -> None:
    session, _ = validate_refresh_session(db, body.refreshToken)
    session.revoked = True
    db.commit()
