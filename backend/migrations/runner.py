from __future__ import annotations

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from backend import models  # noqa: F401
from backend.config import BACKEND_DIR, DATABASE_URL, PROJECT_DIR
from backend.db import Base, engine


INITIAL_REVISION = "20261005_0001"
RECIPE_METADATA_REVISION = "20261009_0002"
RECIPE_VERIFICATION_REVISION = "20261009_0003"
RECIPE_METADATA_COLUMNS = {
    "total_minutes",
    "servings_text",
    "source_revision_url",
    "source_license_name",
    "source_license_url",
    "source_attribution",
    "source_modified",
    "image_author",
    "image_source_url",
    "image_license_name",
    "image_license_url",
}
RECIPE_VERIFICATION_COLUMNS = {
    "content_origin",
    "verification_status",
    "verification_note",
}
RECIPE_REFERENCE_TABLE = "recipe_references"


def _alembic_config() -> Config:
    config = Config(str(PROJECT_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", DATABASE_URL)
    return config


def _stamp_matching_legacy_schema(config: Config) -> None:
    """Adopt databases created by the pre-Alembic MVP without losing data."""

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if not tables or "alembic_version" in tables:
        return

    expected_tables = set(Base.metadata.tables)
    initial_tables = expected_tables - {RECIPE_REFERENCE_TABLE}
    if not initial_tables.issubset(tables):
        missing = ", ".join(sorted(initial_tables - tables))
        raise RuntimeError(
            "Database chưa có migration và thiếu bảng: "
            f"{missing}. Hãy backup rồi tạo database mới hoặc migration thủ công."
        )
    schema_revision = RECIPE_VERIFICATION_REVISION
    for table_name in initial_tables:
        actual_columns = {item["name"] for item in inspector.get_columns(table_name)}
        expected_columns = set(Base.metadata.tables[table_name].columns.keys())
        if table_name != "dishes":
            allowed_columns = {frozenset(expected_columns)}
        else:
            allowed_columns = {
                frozenset(expected_columns),
                frozenset(expected_columns - RECIPE_VERIFICATION_COLUMNS),
                frozenset(
                    expected_columns
                    - RECIPE_VERIFICATION_COLUMNS
                    - RECIPE_METADATA_COLUMNS
                ),
            }
        if frozenset(actual_columns) not in allowed_columns:
            raise RuntimeError(
                f"Schema cũ của bảng {table_name} không khớp model hiện tại; "
                "không tự động stamp để tránh mất dữ liệu."
            )
        if table_name == "dishes":
            if actual_columns == expected_columns - RECIPE_VERIFICATION_COLUMNS - RECIPE_METADATA_COLUMNS:
                schema_revision = INITIAL_REVISION
            elif actual_columns == expected_columns - RECIPE_VERIFICATION_COLUMNS:
                schema_revision = RECIPE_METADATA_REVISION

    has_references = RECIPE_REFERENCE_TABLE in tables
    if schema_revision == RECIPE_VERIFICATION_REVISION and not has_references:
        raise RuntimeError("Schema có metadata xác minh nhưng thiếu bảng recipe_references.")
    if schema_revision != RECIPE_VERIFICATION_REVISION and has_references:
        raise RuntimeError("Schema có bảng recipe_references nhưng thiếu metadata xác minh.")
    command.stamp(config, schema_revision)


def migrate_database() -> None:
    config = _alembic_config()
    _stamp_matching_legacy_schema(config)
    command.upgrade(config, "head")


def main() -> None:
    migrate_database()
    print("Database migration is up to date.")


if __name__ == "__main__":
    main()
