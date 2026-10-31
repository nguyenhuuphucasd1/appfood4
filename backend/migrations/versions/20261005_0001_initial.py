"""Initial Vị Việt MVP schema."""

from alembic import op
import sqlalchemy as sa


revision = "20261005_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dishes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("normalized_name", sa.String(length=160), nullable=False),
        sa.Column("aliases_json", sa.Text(), nullable=False),
        sa.Column("region", sa.String(length=80), nullable=True),
        sa.Column("category", sa.String(length=80), nullable=True),
        sa.Column("prep_minutes", sa.Integer(), nullable=True),
        sa.Column("cook_minutes", sa.Integer(), nullable=True),
        sa.Column("difficulty", sa.String(length=40), nullable=True),
        sa.Column("servings", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("image_attribution", sa.Text(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_name", sa.String(length=200), nullable=True),
        sa.Column("published", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dishes_category", "dishes", ["category"], unique=False)
    op.create_index("ix_dishes_difficulty", "dishes", ["difficulty"], unique=False)
    op.create_index("ix_dishes_normalized_name", "dishes", ["normalized_name"], unique=False)
    op.create_index("ix_dishes_published", "dishes", ["published"], unique=False)
    op.create_index("ix_dishes_region", "dishes", ["region"], unique=False)
    op.create_index("ix_dishes_slug", "dishes", ["slug"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("dish_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dish_id"], ["dishes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "dish_id", name="uq_favorite_user_dish"),
    )
    op.create_index("ix_favorites_dish_id", "favorites", ["dish_id"], unique=False)
    op.create_index("ix_favorites_user_id", "favorites", ["user_id"], unique=False)

    op.create_table(
        "prediction_history",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("predicted_dish", sa.String(length=160), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("top3_json", sa.Text(), nullable=False),
        sa.Column("selected_dish", sa.String(length=160), nullable=True),
        sa.Column("image_stored", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_prediction_history_created_at", "prediction_history", ["created_at"], unique=False
    )
    op.create_index(
        "ix_prediction_history_user_id", "prediction_history", ["user_id"], unique=False
    )

    op.create_table(
        "recipe_ingredients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dish_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("quantity", sa.String(length=80), nullable=True),
        sa.Column("unit", sa.String(length=80), nullable=True),
        sa.ForeignKeyConstraint(["dish_id"], ["dishes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_recipe_ingredients_dish_id", "recipe_ingredients", ["dish_id"], unique=False
    )

    op.create_table(
        "recipe_steps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dish_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("instruction", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["dish_id"], ["dishes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recipe_steps_dish_id", "recipe_steps", ["dish_id"], unique=False)

    op.create_table(
        "refresh_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_refresh_sessions_jti", "refresh_sessions", ["jti"], unique=True)
    op.create_index(
        "ix_refresh_sessions_user_id", "refresh_sessions", ["user_id"], unique=False
    )

    op.create_table(
        "prediction_feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("history_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("selected_dish", sa.String(length=160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["history_id"], ["prediction_history.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("history_id", name="uq_feedback_history"),
    )
    op.create_index(
        "ix_prediction_feedback_history_id", "prediction_feedback", ["history_id"], unique=False
    )
    op.create_index(
        "ix_prediction_feedback_user_id", "prediction_feedback", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_table("prediction_feedback")
    op.drop_table("refresh_sessions")
    op.drop_table("recipe_steps")
    op.drop_table("recipe_ingredients")
    op.drop_table("prediction_history")
    op.drop_table("favorites")
    op.drop_table("users")
    op.drop_table("dishes")
