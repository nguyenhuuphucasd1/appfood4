from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from fastapi import Depends, HTTPException, Request, status
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import ACCESS_TOKEN_MINUTES, AUTH_SECRET_KEY, REFRESH_TOKEN_DAYS
from backend.db import get_db
from backend.models import RefreshSession, User


ALGORITHM = "HS256"
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def _token(user_id: int, token_type: str, expires_delta: timedelta, jti: str | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": jti or uuid4().hex,
    }
    return jwt.encode(payload, AUTH_SECRET_KEY, algorithm=ALGORITHM)


def create_token_pair(db: Session, user: User, *, commit: bool = True) -> tuple[str, str]:
    jti = uuid4().hex
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_DAYS)
    session = RefreshSession(jti=jti, user_id=user.id, expires_at=expires_at)
    db.add(session)
    if commit:
        db.commit()
    return (
        _token(user.id, "access", timedelta(minutes=ACCESS_TOKEN_MINUTES)),
        _token(user.id, "refresh", timedelta(days=REFRESH_TOKEN_DAYS), jti=jti),
    )


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            AUTH_SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "iat", "sub", "type", "jti"]},
        )
        if payload.get("type") != expected_type:
            raise ValueError("Wrong token type")
        user_id = int(payload["sub"])
        if user_id < 1:
            raise ValueError("Invalid subject")
        jti = payload["jti"]
        if not isinstance(jti, str) or not jti:
            raise ValueError("Invalid token id")
        payload["user_id"] = user_id
        return payload
    except (jwt.PyJWTError, KeyError, TypeError, ValueError, OverflowError) as exc:
        raise HTTPException(status_code=401, detail="Phiên đăng nhập không hợp lệ.") from exc


def bearer_token(request: Request) -> str | None:
    header = request.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return None


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = bearer_token(request)
    if not token:
        return None
    payload = decode_token(token, "access")
    return db.get(User, payload["user_id"])


def get_current_user(user: User | None = Depends(get_optional_user)) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bạn cần đăng nhập để sử dụng chức năng này.",
        )
    return user


def validate_refresh_session(db: Session, token: str) -> tuple[RefreshSession, User]:
    payload = decode_token(token, "refresh")
    session = db.scalar(select(RefreshSession).where(RefreshSession.jti == payload["jti"]))
    if session is None or session.revoked:
        raise HTTPException(status_code=401, detail="Phiên làm mới đã hết hiệu lực.")
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Phiên làm mới đã hết hạn.")
    user = db.get(User, payload["user_id"])
    if user is None or user.id != session.user_id:
        raise HTTPException(status_code=401, detail="Tài khoản không còn tồn tại.")
    return session, user
