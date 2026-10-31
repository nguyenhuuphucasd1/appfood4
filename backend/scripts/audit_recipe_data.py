from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.catalog import DISH_NAMES, slugify
from backend.config import PROJECT_DIR
from backend.db import SessionLocal
from backend.migrations.runner import migrate_database
from backend.models import Dish


MANIFEST = PROJECT_DIR / "backend" / "data" / "recipes" / "media_manifest.json"
MEDIA_DIR = PROJECT_DIR / "backend" / "static" / "dishes"


def _database_counts(path: Path) -> dict[str, int]:
    with sqlite3.connect(path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        return {
            name: connection.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            for name in ("dishes", "users", "favorites", "prediction_history")
            if name in tables
        }


def audit(backup: Path | None = None) -> dict:
    migrate_database()
    expected_slugs = {slugify(name) for name in DISH_NAMES}
    manifest_items = json.loads(MANIFEST.read_text(encoding="utf-8"))["items"]
    manifest = {item["slug"]: item for item in manifest_items}
    errors: list[str] = []

    if len(manifest_items) != 38 or len(manifest) != 38:
        errors.append("Manifest phải có đúng 38 slug duy nhất")
    if set(manifest) != expected_slugs:
        errors.append("Slug trong manifest không khớp danh mục 38 món")

    with SessionLocal() as db:
        dishes = db.scalars(
            select(Dish).options(
                selectinload(Dish.ingredients),
                selectinload(Dish.steps),
                selectinload(Dish.references),
            )
        ).all()
        if len(dishes) != 38 or {dish.slug for dish in dishes} != expected_slugs:
            errors.append("Database không có đúng 38 món trong danh mục")
        for dish in dishes:
            if not dish.published:
                errors.append(f"{dish.slug}: chưa published")
            if not dish.ingredients or not dish.steps:
                errors.append(f"{dish.slug}: thiếu nguyên liệu hoặc bước làm")
            if dish.prep_minutes is None or dish.prep_minutes < 0:
                errors.append(f"{dish.slug}: thiếu hoặc sai prepMinutes")
            if dish.cook_minutes is None or dish.cook_minutes < 0:
                errors.append(f"{dish.slug}: thiếu hoặc sai cookMinutes")
            if dish.total_minutes is None or dish.total_minutes <= 0:
                errors.append(f"{dish.slug}: thiếu hoặc sai totalMinutes")
            elif (
                dish.prep_minutes is not None
                and dish.cook_minutes is not None
                and dish.total_minutes < dish.prep_minutes + dish.cook_minutes
            ):
                errors.append(f"{dish.slug}: totalMinutes nhỏ hơn sơ chế + nấu")
            if not (dish.servings_text or "").strip():
                errors.append(f"{dish.slug}: thiếu servingsText")
            minimum = 2 if dish.content_origin == "original_synthesis" else 1
            if len(dish.references) < minimum:
                errors.append(f"{dish.slug}: thiếu nguồn tham khảo")
            item = manifest.get(dish.slug)
            if item is None:
                continue
            expected_url = f"/media/dishes/{dish.slug}.webp"
            if dish.image_url != expected_url:
                errors.append(f"{dish.slug}: imageUrl không khớp media cục bộ")
            image_path = MEDIA_DIR / f"{dish.slug}.webp"
            if not image_path.is_file():
                errors.append(f"{dish.slug}: thiếu file WebP")
                continue
            digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
            if digest != item.get("sha256"):
                errors.append(f"{dish.slug}: SHA-256 không khớp")
            with Image.open(image_path) as image:
                if image.format != "WEBP" or max(image.size) > 1600:
                    errors.append(f"{dish.slug}: định dạng hoặc kích thước ảnh sai")

        origins = {
            "translated_open_source": sum(
                dish.content_origin == "translated_open_source" for dish in dishes
            ),
            "original_synthesis": sum(
                dish.content_origin == "original_synthesis" for dish in dishes
            ),
        }
        if origins != {"translated_open_source": 8, "original_synthesis": 30}:
            errors.append(f"Phân bố nguồn nội dung sai: {origins}")
        current_ids = {dish.slug: dish.id for dish in dishes}
        metadata_complete = sum(
            dish.prep_minutes is not None
            and dish.cook_minutes is not None
            and dish.total_minutes is not None
            and dish.total_minutes > 0
            and bool((dish.servings_text or "").strip())
            for dish in dishes
        )

    preservation = None
    if backup is not None:
        current_db = PROJECT_DIR / "backend" / "data" / "vi_viet.db"
        before = _database_counts(backup)
        after = _database_counts(current_db)
        preserved_tables = ("dishes", "users", "favorites", "prediction_history")
        for table in preserved_tables:
            if before.get(table, 0) != after.get(table, 0):
                errors.append(
                    f"Số dòng {table} thay đổi: {before.get(table, 0)} -> {after.get(table, 0)}"
                )
        with sqlite3.connect(backup) as connection:
            old_ids = dict(connection.execute("SELECT slug, id FROM dishes"))
        if old_ids != current_ids:
            errors.append("ID món đã thay đổi sau import")
        preservation = {"before": before, "after": after, "dishIdsPreserved": old_ids == current_ids}

    return {
        "ok": not errors,
        "dishes": 38,
        "published": 38,
        "images": len(manifest),
        "metadataComplete": metadata_complete,
        "origins": origins,
        "preservation": preservation,
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit dữ liệu công thức Vị Việt")
    parser.add_argument("--backup", type=Path)
    args = parser.parse_args()
    result = audit(args.backup)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
