from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from backend.catalog import normalize_text
from backend.db import get_db
from backend.models import Dish, Favorite, User
from backend.security import get_current_user, get_optional_user
from backend.serializers import dish_json


router = APIRouter(tags=["dishes"])


def favorite_ids(db: Session, user: User | None) -> set[int]:
    if user is None:
        return set()
    return set(db.scalars(select(Favorite.dish_id).where(Favorite.user_id == user.id)).all())


@router.get("/dishes")
def list_dishes(
    q: str = "",
    region: str | None = None,
    category: str | None = None,
    difficulty: str | None = None,
    maxMinutes: int | None = Query(default=None, ge=1, le=1440),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> dict:
    statement = select(Dish)
    normalized = normalize_text(q)
    if normalized:
        statement = statement.where(
            or_(Dish.normalized_name.contains(normalized), Dish.aliases_json.contains(normalized))
        )
    if region:
        statement = statement.where(Dish.region == region)
    if category:
        statement = statement.where(Dish.category == category)
    if difficulty:
        statement = statement.where(Dish.difficulty == difficulty)
    if maxMinutes:
        statement = statement.where(
            or_(
                and_(
                    Dish.total_minutes.is_not(None),
                    Dish.total_minutes <= maxMinutes,
                ),
                and_(
                    Dish.total_minutes.is_(None),
                    Dish.prep_minutes.is_not(None),
                    Dish.cook_minutes.is_not(None),
                    Dish.prep_minutes + Dish.cook_minutes <= maxMinutes,
                ),
            )
        )
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    dishes = db.scalars(statement.order_by(Dish.name).offset((page - 1) * limit).limit(limit)).all()
    favorites = favorite_ids(db, user)
    return {
        "items": [dish_json(item, item.id in favorites) for item in dishes],
        "page": page,
        "limit": limit,
        "total": total,
    }


@router.get("/dishes/{slug}")
def get_dish(
    slug: str,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> dict:
    dish = db.scalar(
        select(Dish)
        .options(
            selectinload(Dish.ingredients),
            selectinload(Dish.steps),
            selectinload(Dish.references),
        )
        .where(Dish.slug == slug)
    )
    if dish is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy món ăn.")
    return dish_json(dish, dish.id in favorite_ids(db, user), include_recipe=True)


class FavoriteBody(BaseModel):
    dishSlug: str


@router.get("/favorites")
def list_favorites(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    favorites = db.scalars(
        select(Favorite).options(selectinload(Favorite.dish)).where(Favorite.user_id == user.id)
    ).all()
    return {"items": [dish_json(item.dish, True) for item in favorites]}


@router.post("/favorites", status_code=201)
def add_favorite(
    body: FavoriteBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    slug = body.dishSlug.strip()
    if not slug:
        raise HTTPException(status_code=422, detail="dishSlug không được để trống.")
    dish = db.scalar(select(Dish).where(Dish.slug == slug))
    if dish is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy món ăn.")
    existing = db.scalar(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.dish_id == dish.id)
    )
    if existing is None:
        db.add(Favorite(user_id=user.id, dish_id=dish.id))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
    return dish_json(dish, True)


@router.delete("/favorites/{slug}", status_code=204)
def remove_favorite(
    slug: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    favorite = db.scalar(
        select(Favorite)
        .join(Dish)
        .where(Favorite.user_id == user.id, Dish.slug == slug)
    )
    if favorite is not None:
        db.delete(favorite)
        db.commit()
