"""Add recipe origin, verification, and reference metadata."""

from alembic import op
import sqlalchemy as sa


revision = "20261009_0003"
down_revision = "20261009_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("dishes") as batch:
        batch.add_column(sa.Column("content_origin", sa.String(length=40), nullable=True))
        batch.add_column(sa.Column("verification_status", sa.String(length=40), nullable=True))
        batch.add_column(sa.Column("verification_note", sa.Text(), nullable=True))

    op.create_table(
        "recipe_references",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dish_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("publisher", sa.String(length=200), nullable=False),
        sa.Column("accessed_at", sa.String(length=10), nullable=False),
        sa.ForeignKeyConstraint(["dish_id"], ["dishes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_recipe_references_dish_id",
        "recipe_references",
        ["dish_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("recipe_references")
    with op.batch_alter_table("dishes") as batch:
        batch.drop_column("verification_note")
        batch.drop_column("verification_status")
        batch.drop_column("content_origin")
