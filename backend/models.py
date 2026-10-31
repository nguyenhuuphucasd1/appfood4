from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RefreshSession(Base):
    __tablename__ = "refresh_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    jti: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class Dish(Base):
    __tablename__ = "dishes"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    normalized_name: Mapped[str] = mapped_column(String(160), index=True)
    aliases_json: Mapped[str] = mapped_column(Text, default="[]")
    region: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    prep_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cook_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    servings: Mapped[int | None] = mapped_column(Integer, nullable=True)
    servings_text: Mapped[str | None] = mapped_column(String(80), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_attribution: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source_revision_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_license_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source_license_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_attribution: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_modified: Mapped[bool] = mapped_column(Boolean, default=False)
    image_author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    image_source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_license_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    image_license_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_origin: Mapped[str | None] = mapped_column(String(40), nullable=True)
    verification_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    verification_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    ingredients: Mapped[list[RecipeIngredient]] = relationship(
        cascade="all, delete-orphan", order_by="RecipeIngredient.position"
    )
    steps: Mapped[list[RecipeStep]] = relationship(
        cascade="all, delete-orphan", order_by="RecipeStep.position"
    )
    references: Mapped[list[RecipeReference]] = relationship(
        cascade="all, delete-orphan", order_by="RecipeReference.position"
    )


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(200))
    quantity: Mapped[str | None] = mapped_column(String(80), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(80), nullable=True)


class RecipeStep(Base):
    __tablename__ = "recipe_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    instruction: Mapped[str] = mapped_column(Text)


class RecipeReference(Base):
    __tablename__ = "recipe_references"

    id: Mapped[int] = mapped_column(primary_key=True)
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(240))
    url: Mapped[str] = mapped_column(Text)
    publisher: Mapped[str] = mapped_column(String(200))
    accessed_at: Mapped[str] = mapped_column(String(10))


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "dish_id", name="uq_favorite_user_dish"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    dish_id: Mapped[int] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    dish: Mapped[Dish] = relationship()


class PredictionHistory(Base):
    __tablename__ = "prediction_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    predicted_dish: Mapped[str] = mapped_column(String(160))
    confidence: Mapped[float] = mapped_column(Float)
    top3_json: Mapped[str] = mapped_column(Text)
    selected_dish: Mapped[str | None] = mapped_column(String(160), nullable=True)
    image_stored: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class PredictionFeedback(Base):
    __tablename__ = "prediction_feedback"
    __table_args__ = (UniqueConstraint("history_id", name="uq_feedback_history"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    history_id: Mapped[str] = mapped_column(
        ForeignKey("prediction_history.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    selected_dish: Mapped[str] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
