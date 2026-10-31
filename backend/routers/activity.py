from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models import PredictionFeedback, PredictionHistory, User
from backend.security import get_current_user
from backend.serializers import history_json


router = APIRouter(tags=["activity"])


@router.get("/history")
def history(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    items = db.scalars(
        select(PredictionHistory)
        .where(PredictionHistory.user_id == user.id)
        .order_by(PredictionHistory.created_at.desc())
        .limit(100)
    ).all()
    return {"items": [history_json(item) for item in items]}


@router.delete("/history", status_code=204)
def clear_history(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    db.execute(delete(PredictionHistory).where(PredictionHistory.user_id == user.id))
    db.commit()


@router.delete("/history/{history_id}", status_code=204)
def delete_history(
    history_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    item = db.scalar(
        select(PredictionHistory).where(
            PredictionHistory.id == history_id, PredictionHistory.user_id == user.id
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch sử.")
    db.delete(item)
    db.commit()


class FeedbackBody(BaseModel):
    selectedDish: str = Field(min_length=1, max_length=160)


@router.post("/predictions/{history_id}/feedback")
def feedback(
    history_id: str,
    body: FeedbackBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    item = db.scalar(
        select(PredictionHistory).where(
            PredictionHistory.id == history_id, PredictionHistory.user_id == user.id
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy lần nhận diện.")
    selected = body.selectedDish.strip()
    if not selected:
        raise HTTPException(status_code=422, detail="Tên món đã chọn không được để trống.")
    item.selected_dish = selected
    existing = db.scalar(select(PredictionFeedback).where(PredictionFeedback.history_id == history_id))
    if existing:
        existing.selected_dish = selected
    else:
        db.add(PredictionFeedback(history_id=history_id, user_id=user.id, selected_dish=selected))
    db.commit()
    return history_json(item)
