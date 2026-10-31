from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import select

from backend.catalog import normalize_text, seed_catalog, slugify
from backend.config import DATABASE_URL, PROJECT_DIR
from backend.db import SessionLocal
from backend.migrations.runner import migrate_database
from backend.models import Dish, RecipeIngredient, RecipeReference, RecipeStep


CSV_JSON_LIST_FIELDS = ("aliases", "ingredients", "steps", "references")
CSV_INTEGER_FIELDS = ("prepMinutes", "cookMinutes", "totalMinutes", "servings")
REQUIRED_SOURCE_FIELDS = (
    "name",
    "sourceUrl",
    "sourceName",
    "sourceRevisionUrl",
    "sourceLicenseName",
    "sourceLicenseUrl",
    "sourceAttribution",
)
REQUIRED_IMAGE_FIELDS = (
    "imageAttribution",
    "imageAuthor",
    "imageSourceUrl",
    "imageLicenseName",
    "imageLicenseUrl",
)
REQUIRED_VERIFICATION_FIELDS = (
    "contentOrigin",
    "verificationStatus",
    "verificationNote",
)
ALLOWED_CONTENT_ORIGINS = {"translated_open_source", "original_synthesis"}


def _parse_csv_json_list(raw: str | None, *, field: str, line_number: int) -> list[Any]:
    if raw is None or not raw.strip():
        return []
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Dòng {line_number}: cột {field} phải là một mảng JSON hợp lệ"
        ) from exc
    if not isinstance(value, list):
        raise ValueError(f"Dòng {line_number}: cột {field} phải là một mảng JSON")
    return value


def _parse_csv_integer(raw: str | None, *, field: str, line_number: int) -> int | None:
    if raw is None or not raw.strip():
        return None
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"Dòng {line_number}: cột {field} phải là số nguyên") from exc


def read_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix.casefold() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            records = payload
        elif isinstance(payload, dict):
            records = payload.get("dishes", [])
        else:
            raise ValueError("JSON phải là một mảng công thức hoặc object có mảng 'dishes'")
        if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
            raise ValueError("JSON phải là một mảng công thức hoặc object có mảng 'dishes'")
        return records
    if path.suffix.casefold() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as handle:
            records: list[dict[str, Any]] = []
            for line_number, row in enumerate(csv.DictReader(handle), start=2):
                record: dict[str, Any] = dict(row)
                for field in CSV_JSON_LIST_FIELDS:
                    record[field] = _parse_csv_json_list(
                        row.get(field), field=field, line_number=line_number
                    )
                for field in CSV_INTEGER_FIELDS:
                    record[field] = _parse_csv_integer(
                        row.get(field), field=field, line_number=line_number
                    )
                records.append(record)
            return records
    raise ValueError("Chỉ hỗ trợ file .json hoặc .csv")


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _is_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def read_media_manifest(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("items", []) if isinstance(payload, dict) else []
    if not isinstance(items, list):
        raise ValueError("Media manifest phải có mảng 'items'")
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict) or not str(item.get("slug", "")).strip():
            raise ValueError("Mỗi media item phải có slug")
        result[str(item["slug"])] = item
    return result


def merge_media(
    records: list[dict[str, Any]], media: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for record in records:
        item = dict(record)
        slug = str(item.get("slug") or slugify(str(item.get("name", ""))))
        if slug in media:
            for key, value in media[slug].items():
                if key not in {"slug", "commonsFileTitle", "sha256", "downloadUrl"}:
                    item[key] = value
        merged.append(item)
    return merged


def validate(record: dict[str, Any]) -> None:
    missing = [key for key in REQUIRED_SOURCE_FIELDS if not str(record.get(key, "")).strip()]
    if missing:
        raise ValueError(f"{record.get('name', '<không tên>')}: thiếu {', '.join(missing)}")
    source_url = str(record["sourceUrl"]).strip()
    if not _is_http_url(source_url):
        raise ValueError(f"{record['name']}: sourceUrl phải là URL HTTP(S)")
    for field in ("sourceRevisionUrl", "sourceLicenseUrl"):
        if not _is_http_url(str(record[field]).strip()):
            raise ValueError(f"{record['name']}: {field} phải là URL HTTP(S)")
    missing_verification = [
        key for key in REQUIRED_VERIFICATION_FIELDS if not str(record.get(key, "")).strip()
    ]
    if missing_verification:
        raise ValueError(
            f"{record['name']}: thiếu {', '.join(missing_verification)}"
        )
    content_origin = str(record["contentOrigin"]).strip()
    if content_origin not in ALLOWED_CONTENT_ORIGINS:
        raise ValueError(
            f"{record['name']}: contentOrigin phải là translated_open_source "
            "hoặc original_synthesis"
        )
    source_modified = record.get("sourceModified")
    if not isinstance(source_modified, bool):
        raise ValueError(f"{record['name']}: sourceModified phải là boolean")
    if content_origin == "translated_open_source" and source_modified is not True:
        raise ValueError(
            f"{record['name']}: bản dịch từ nguồn mở phải có sourceModified=true"
        )
    if content_origin == "original_synthesis" and source_modified is not False:
        raise ValueError(
            f"{record['name']}: nội dung biên soạn mới phải có sourceModified=false"
        )

    references = record.get("references", [])
    minimum_references = 1 if content_origin == "translated_open_source" else 2
    if not isinstance(references, list) or len(references) < minimum_references:
        raise ValueError(
            f"{record['name']}: cần ít nhất {minimum_references} nguồn tham khảo"
        )
    for reference in references:
        if not isinstance(reference, dict):
            raise ValueError(f"{record['name']}: mỗi nguồn tham khảo phải là object")
        missing_reference = [
            key
            for key in ("name", "url", "publisher", "accessedAt")
            if not str(reference.get(key, "")).strip()
        ]
        if missing_reference:
            raise ValueError(
                f"{record['name']}: nguồn tham khảo thiếu {', '.join(missing_reference)}"
            )
        if not _is_http_url(str(reference["url"]).strip()):
            raise ValueError(f"{record['name']}: URL nguồn tham khảo không hợp lệ")
        if not _is_iso_date(str(reference["accessedAt"]).strip()):
            raise ValueError(
                f"{record['name']}: accessedAt phải có định dạng YYYY-MM-DD"
            )

    metadata_source_url = str(record.get("metadataSourceUrl") or "").strip()
    if not _is_http_url(metadata_source_url):
        raise ValueError(
            f"{record['name']}: metadataSourceUrl phải là URL HTTP(S)"
        )
    reference_urls = {str(item["url"]).strip() for item in references}
    if metadata_source_url not in reference_urls:
        raise ValueError(
            f"{record['name']}: nguồn thời gian/khẩu phần phải có trong references"
        )

    aliases = record.get("aliases", [])
    if not isinstance(aliases, list) or any(not isinstance(item, str) for item in aliases):
        raise ValueError(f"{record['name']}: aliases phải là một mảng chuỗi")

    ingredients = record.get("ingredients", [])
    if not isinstance(ingredients, list) or not ingredients:
        raise ValueError(f"{record['name']}: ingredients phải là một mảng JSON không rỗng")
    for item in ingredients:
        if not isinstance(item, dict) or not str(item.get("name", "")).strip():
            raise ValueError(f"{record['name']}: mỗi nguyên liệu phải có name")

    steps = record.get("steps", [])
    if not isinstance(steps, list) or not steps or any(
        not isinstance(item, str) or not item.strip() for item in steps
    ):
        raise ValueError(f"{record['name']}: steps phải là một mảng chuỗi không rỗng")

    for field in CSV_INTEGER_FIELDS:
        value = record.get(field)
        if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
            raise ValueError(f"{record['name']}: {field} phải là số nguyên")
        if value is not None and value < 0:
            raise ValueError(f"{record['name']}: {field} không được âm")

    for field in ("prepMinutes", "cookMinutes", "totalMinutes"):
        if record.get(field) is None:
            raise ValueError(f"{record['name']}: thiếu {field}")
    prep_minutes = record["prepMinutes"]
    cook_minutes = record["cookMinutes"]
    total_minutes = record["totalMinutes"]
    if total_minutes <= 0:
        raise ValueError(f"{record['name']}: totalMinutes phải lớn hơn 0")
    if total_minutes < prep_minutes + cook_minutes:
        raise ValueError(
            f"{record['name']}: totalMinutes không được nhỏ hơn prepMinutes + cookMinutes"
        )
    if record.get("servings") is not None and record["servings"] <= 0:
        raise ValueError(f"{record['name']}: servings phải lớn hơn 0 khi được cung cấp")

    servings_text = record.get("servingsText")
    if not isinstance(servings_text, str) or not servings_text.strip():
        raise ValueError(f"{record['name']}: servingsText phải là chuỗi không rỗng")

    image_url = str(record.get("imageUrl") or "").strip()
    if not image_url:
        raise ValueError(f"{record['name']}: thiếu imageUrl")
    if not _is_http_url(image_url):
        if not image_url.startswith("/media/dishes/") or ".." in image_url:
            raise ValueError(
                f"{record['name']}: imageUrl phải là URL HTTP(S) hoặc /media/dishes/... an toàn"
            )
    missing_image = [
        key for key in REQUIRED_IMAGE_FIELDS if not str(record.get(key, "")).strip()
    ]
    if missing_image:
        raise ValueError(f"{record['name']}: ảnh thiếu {', '.join(missing_image)}")
    for field in ("imageSourceUrl", "imageLicenseUrl"):
        if not _is_http_url(str(record[field]).strip()):
            raise ValueError(f"{record['name']}: {field} phải là URL HTTP(S)")
    license_name = str(record["imageLicenseName"]).casefold()
    if not (
        "public domain" in license_name
        or "cc0" in license_name
        or "cc by" in license_name
    ) or "-nc" in license_name or "-nd" in license_name:
        raise ValueError(f"{record['name']}: giấy phép ảnh không nằm trong danh sách cho phép")


def validation_report(records: list[dict[str, Any]]) -> dict[str, Any]:
    valid_slugs: list[str] = []
    errors: list[dict[str, Any]] = []
    seen_slugs: set[str] = set()
    for index, record in enumerate(records, start=1):
        slug = str(record.get("slug") or slugify(str(record.get("name", ""))))
        if slug in seen_slugs:
            errors.append(
                {"index": index, "slug": slug, "error": f"{slug}: slug bị trùng"}
            )
            continue
        seen_slugs.add(slug)
        try:
            validate(record)
        except ValueError as exc:
            errors.append({"index": index, "slug": slug, "error": str(exc)})
        else:
            valid_slugs.append(slug)
    return {
        "valid": len(valid_slugs),
        "validSlugs": valid_slugs,
        "invalid": len(errors),
        "errors": errors,
    }


def import_records(records: list[dict[str, Any]]) -> int:
    for record in records:
        validate(record)
    migrate_database()
    imported = 0
    with SessionLocal() as db:
        seed_catalog(db)
        for record in records:
            slug = str(record.get("slug") or slugify(str(record["name"])))
            dish = db.scalar(select(Dish).where(Dish.slug == slug))
            if dish is None:
                dish = Dish(slug=slug, name=str(record["name"]), normalized_name=normalize_text(str(record["name"])))
                db.add(dish)
                db.flush()
            dish.name = str(record["name"]).strip()
            dish.normalized_name = normalize_text(dish.name)
            dish.aliases_json = json.dumps(
                [item.strip() for item in record.get("aliases", []) if item.strip()],
                ensure_ascii=False,
            )
            dish.region = record.get("region") or None
            dish.category = record.get("category") or None
            dish.prep_minutes = record.get("prepMinutes")
            dish.cook_minutes = record.get("cookMinutes")
            dish.total_minutes = record.get("totalMinutes")
            dish.difficulty = record.get("difficulty") or None
            dish.servings = record.get("servings")
            dish.servings_text = str(record.get("servingsText") or "").strip() or None
            dish.description = record.get("description") or None
            dish.image_url = str(record.get("imageUrl") or "").strip() or None
            dish.image_attribution = str(record.get("imageAttribution") or "").strip() or None
            dish.source_url = str(record["sourceUrl"]).strip()
            dish.source_name = str(record["sourceName"]).strip()
            dish.source_revision_url = str(record["sourceRevisionUrl"]).strip()
            dish.source_license_name = str(record["sourceLicenseName"]).strip()
            dish.source_license_url = str(record["sourceLicenseUrl"]).strip()
            dish.source_attribution = str(record["sourceAttribution"]).strip()
            dish.source_modified = bool(record["sourceModified"])
            dish.image_author = str(record.get("imageAuthor") or "").strip() or None
            dish.image_source_url = str(record.get("imageSourceUrl") or "").strip() or None
            dish.image_license_name = str(record.get("imageLicenseName") or "").strip() or None
            dish.image_license_url = str(record.get("imageLicenseUrl") or "").strip() or None
            dish.content_origin = str(record["contentOrigin"]).strip()
            dish.verification_status = str(record["verificationStatus"]).strip()
            dish.verification_note = str(record["verificationNote"]).strip()
            dish.published = True
            dish.ingredients.clear()
            dish.steps.clear()
            dish.references.clear()
            for index, item in enumerate(record.get("ingredients", []), 1):
                dish.ingredients.append(
                    RecipeIngredient(
                        position=index,
                        name=str(item["name"]).strip(),
                        quantity=str(item.get("quantity") or "") or None,
                        unit=str(item.get("unit") or "") or None,
                    )
                )
            for index, instruction in enumerate(record.get("steps", []), 1):
                dish.steps.append(RecipeStep(position=index, instruction=instruction.strip()))
            for index, reference in enumerate(record.get("references", []), 1):
                dish.references.append(
                    RecipeReference(
                        position=index,
                        name=str(reference["name"]).strip(),
                        url=str(reference["url"]).strip(),
                        publisher=str(reference["publisher"]).strip(),
                        accessed_at=str(reference["accessedAt"]).strip(),
                    )
                )
            imported += 1
        db.commit()
    return imported


def backup_sqlite_database() -> Path | None:
    prefix = "sqlite:///"
    if not DATABASE_URL.startswith(prefix):
        return None
    raw_path = DATABASE_URL[len(prefix) :]
    source = Path(raw_path)
    if not source.is_absolute():
        source = (PROJECT_DIR / source).resolve()
    if not source.is_file():
        return None
    backup_dir = PROJECT_DIR / "artifacts" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination = backup_dir / f"vi_viet-before-recipes-{stamp}.db"
    with sqlite3.connect(source) as source_db, sqlite3.connect(destination) as backup_db:
        source_db.backup(backup_db)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description="Import sourced recipes into Vị Việt")
    parser.add_argument("input", type=Path, nargs="+")
    parser.add_argument("--media-manifest", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    records = [record for path in args.input for record in read_records(path)]
    records = merge_media(records, read_media_manifest(args.media_manifest))
    report = validation_report(records)
    if report["invalid"]:
        print(json.dumps({**report, "imported": 0, "dryRun": args.dry_run}, ensure_ascii=False))
        raise SystemExit(1)
    if args.dry_run:
        print(json.dumps({**report, "imported": 0, "dryRun": True}, ensure_ascii=False))
        return
    backup = backup_sqlite_database()
    imported = import_records(records)
    print(
        json.dumps(
            {
                **report,
                "imported": imported,
                "dryRun": False,
                "backup": str(backup) if backup else None,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
