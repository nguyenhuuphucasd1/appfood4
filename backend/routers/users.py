from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models import User
from backend.security import get_current_user
from backend.serializers import user_json


router = APIRouter(prefix="/users", tags=["users"])


class UpdateProfileBody(BaseModel):
    fullName: str = Field(min_length=2, max_length=120)


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict:
    return user_json(user)


@router.patch("/me")
def update_me(
    body: UpdateProfileBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    full_name = body.fullName.strip()
    if len(full_name) < 2:
        raise HTTPException(status_code=422, detail="Họ và tên phải có ít nhất 2 ký tự.")
    user.full_name = full_name
    db.commit()
    db.refresh(user)
    return user_json(user)
