"""Add recipe and image licensing metadata."""

from alembic import op
import sqlalchemy as sa


revision = "20261009_0002"
down_revision = "20261005_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("dishes") as batch:
        batch.add_column(sa.Column("total_minutes", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("servings_text", sa.String(length=80), nullable=True))
        batch.add_column(sa.Column("source_revision_url", sa.Text(), nullable=True))
        batch.add_column(sa.Column("source_license_name", sa.String(length=120), nullable=True))
        batch.add_column(sa.Column("source_license_url", sa.Text(), nullable=True))
        batch.add_column(sa.Column("source_attribution", sa.Text(), nullable=True))
        batch.add_column(
            sa.Column("source_modified", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.add_column(sa.Column("image_author", sa.String(length=200), nullable=True))
        batch.add_column(sa.Column("image_source_url", sa.Text(), nullable=True))
        batch.add_column(sa.Column("image_license_name", sa.String(length=120), nullable=True))
        batch.add_column(sa.Column("image_license_url", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("dishes") as batch:
        batch.drop_column("image_license_url")
        batch.drop_column("image_license_name")
        batch.drop_column("image_source_url")
        batch.drop_column("image_author")
        batch.drop_column("source_modified")
        batch.drop_column("source_attribution")
        batch.drop_column("source_license_url")
        batch.drop_column("source_license_name")
        batch.drop_column("source_revision_url")
        batch.drop_column("servings_text")
        batch.drop_column("total_minutes")
