from __future__ import annotations

import argparse
import hashlib
import html
import io
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests
from PIL import Image, ImageOps


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


PROJECT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_DIR / "backend"
DEFAULT_CATALOG = BACKEND_DIR / "data" / "recipes" / "open_recipes.vi.json"
DEFAULT_OUTPUT = BACKEND_DIR / "data" / "recipes" / "media_manifest.json"
MEDIA_DIR = BACKEND_DIR / "static" / "dishes"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "ViVietRecipeImporter/1.0 (educational project; Wikimedia attribution audit)"
MAX_DOWNLOAD_BYTES = 25 * 1024 * 1024
PUBLIC_DOMAIN_MARK_URL = "https://creativecommons.org/publicdomain/mark/1.0/"


def _clean_html(value: str | None) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value or "")
    return " ".join(html.unescape(without_tags).split())


def _is_allowed_license(name: str) -> bool:
    normalized = name.casefold()
    allowed = "public domain" in normalized or "cc0" in normalized or "cc by" in normalized
    return allowed and "-nc" not in normalized and "-nd" not in normalized


def _ensure_project_path(path: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(PROJECT_DIR):
        raise ValueError(f"Chỉ được ghi file trong {PROJECT_DIR}: {resolved}")
    return resolved


def fetch_metadata(file_title: str) -> dict[str, Any]:
    response = requests.get(
        COMMONS_API,
        params={
            "action": "query",
            "format": "json",
            "formatversion": 2,
            "prop": "imageinfo",
            "titles": file_title,
            "iiprop": "url|size|extmetadata",
            "iiurlwidth": 320,
        },
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    response.raise_for_status()
    pages = response.json().get("query", {}).get("pages", [])
    if not pages or pages[0].get("missing"):
        raise ValueError(f"Không tìm thấy file Commons: {file_title}")
    info = (pages[0].get("imageinfo") or [{}])[0]
    metadata = info.get("extmetadata") or {}
    license_name = str(metadata.get("LicenseShortName", {}).get("value") or "").strip()
    license_url = str(metadata.get("LicenseUrl", {}).get("value") or "").strip()
    if "public domain" in license_name.casefold() and not license_url:
        license_url = PUBLIC_DOMAIN_MARK_URL
    author = _clean_html(metadata.get("Artist", {}).get("value"))
    source_url = str(info.get("descriptionurl") or "").strip()
    download_url = str(info.get("thumburl") or info.get("url") or "").strip()
    if not all((license_name, license_url, author, source_url, download_url)):
        raise ValueError(f"Metadata ảnh chưa đầy đủ: {file_title}")
    if not _is_allowed_license(license_name):
        raise ValueError(f"Giấy phép ảnh không được chấp nhận: {file_title} ({license_name})")
    return {
        "commonsFileTitle": file_title,
        "downloadUrl": download_url,
        "imageAuthor": author,
        "imageSourceUrl": source_url,
        "imageLicenseName": license_name,
        "imageLicenseUrl": license_url,
    }


def fetch_metadata_batch(file_titles: list[str]) -> dict[str, dict[str, Any]]:
    """Resolve all Commons files in one API call to avoid per-file rate limiting."""

    response = requests.get(
        COMMONS_API,
        params={
            "action": "query",
            "format": "json",
            "formatversion": 2,
            "prop": "imageinfo",
            "titles": "|".join(file_titles),
            "iiprop": "url|size|extmetadata",
            "iiurlwidth": 320,
        },
        headers={"User-Agent": USER_AGENT},
        timeout=60,
    )
    response.raise_for_status()
    requested_by_key = {
        title.replace("_", " ").casefold(): title for title in file_titles
    }
    result: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    invalid: list[str] = []
    for page in response.json().get("query", {}).get("pages", []):
        resolved_title = str(page.get("title") or "")
        original_title = requested_by_key.get(
            resolved_title.replace("_", " ").casefold(), resolved_title
        )
        if page.get("missing"):
            missing.append(original_title)
            continue
        info = (page.get("imageinfo") or [{}])[0]
        metadata = info.get("extmetadata") or {}
        license_name = str(metadata.get("LicenseShortName", {}).get("value") or "").strip()
        license_url = str(metadata.get("LicenseUrl", {}).get("value") or "").strip()
        if "public domain" in license_name.casefold() and not license_url:
            license_url = PUBLIC_DOMAIN_MARK_URL
        author = _clean_html(metadata.get("Artist", {}).get("value"))
        source_url = str(info.get("descriptionurl") or "").strip()
        download_url = str(info.get("thumburl") or info.get("url") or "").strip()
        if not all((license_name, license_url, author, source_url, download_url)):
            invalid.append(f"{original_title} (metadata chưa đầy đủ)")
            continue
        if not _is_allowed_license(license_name):
            invalid.append(f"{original_title} (giấy phép {license_name})")
            continue
        result[original_title] = {
            "commonsFileTitle": resolved_title,
            "downloadUrl": download_url,
            "imageAuthor": author,
            "imageSourceUrl": source_url,
            "imageLicenseName": license_name,
            "imageLicenseUrl": license_url,
        }
    if missing or invalid:
        details = []
        if missing:
            details.append("không tìm thấy: " + ", ".join(sorted(missing)))
        if invalid:
            details.append("không hợp lệ: " + ", ".join(sorted(invalid)))
        raise ValueError("Ảnh Commons thất bại audit; " + "; ".join(details))
    if len(result) != len(file_titles):
        unresolved = sorted(set(file_titles) - set(result))
        raise ValueError("Không phân giải được file Commons: " + ", ".join(unresolved))
    return result


def download_and_convert(url: str, destination: Path) -> str:
    # Commons appends analytics parameters that can share a cached 429 response.
    # The canonical media URL is stable without them.
    url = url.split("?", 1)[0]
    response = None
    for attempt in range(6):
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=60)
        if response.status_code != 429 and response.status_code < 500:
            break
        if attempt == 5:
            response.raise_for_status()
        retry_after = response.headers.get("Retry-After")
        wait_seconds = float(retry_after) if retry_after else min(2 ** (attempt + 1), 16)
        time.sleep(wait_seconds)
    assert response is not None
    response.raise_for_status()
    content = response.content
    if len(content) > MAX_DOWNLOAD_BYTES:
        raise ValueError(f"Ảnh vượt quá {MAX_DOWNLOAD_BYTES} byte")
    with Image.open(io.BytesIO(content)) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        destination.parent.mkdir(parents=True, exist_ok=True)
        image.save(destination, "WEBP", quality=84, method=6)
    return hashlib.sha256(destination.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Tải ảnh món có giấy phép từ Wikimedia Commons")
    parser.add_argument("--catalog", type=Path, nargs="+", default=[DEFAULT_CATALOG])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    output_path = _ensure_project_path(args.output)
    media_dir = _ensure_project_path(MEDIA_DIR)
    dishes: list[dict[str, Any]] = []
    for raw_catalog_path in args.catalog:
        catalog_path = _ensure_project_path(raw_catalog_path)
        payload = json.loads(catalog_path.read_text(encoding="utf-8"))
        catalog_dishes = payload.get("dishes", [])
        if not isinstance(catalog_dishes, list) or not catalog_dishes:
            raise ValueError(f"Catalog không có mảng dishes: {catalog_path}")
        dishes.extend(catalog_dishes)
    if not isinstance(dishes, list) or not dishes:
        raise ValueError("Catalog không có mảng dishes")

    items = []
    seen_slugs: set[str] = set()
    requested_titles: list[str] = []
    for dish in dishes:
        file_title = str(dish.get("commonsFileTitle") or "").strip()
        if file_title:
            requested_titles.append(file_title)
    if len(requested_titles) != len(set(requested_titles)):
        raise ValueError("Mỗi món phải dùng một ảnh Commons riêng")
    metadata_by_title = fetch_metadata_batch(requested_titles)
    for dish in dishes:
        slug = str(dish.get("slug") or "").strip()
        file_title = str(dish.get("commonsFileTitle") or "").strip()
        if not slug or not file_title:
            raise ValueError("Mỗi món phải có slug và commonsFileTitle")
        if slug in seen_slugs:
            raise ValueError(f"Slug ảnh bị trùng: {slug}")
        seen_slugs.add(slug)
        metadata = metadata_by_title[file_title]
        destination = media_dir / f"{slug}.webp"
        sha256 = download_and_convert(metadata["downloadUrl"], destination)
        items.append(
            {
                "slug": slug,
                **metadata,
                "imageUrl": f"/media/dishes/{slug}.webp",
                "imageAttribution": (
                    f"{metadata['imageAuthor']} · {metadata['imageLicenseName']} · Wikimedia Commons"
                ),
                "sha256": sha256,
            }
        )
        print(f"Đã tải ảnh hợp lệ: {slug}", file=sys.stderr)
        time.sleep(0.75)

    manifest = {
        "provider": "Wikimedia Commons",
        "policy": "Only Public Domain, CC0, CC BY, or CC BY-SA images with complete metadata.",
        "items": items,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"downloaded": len(items), "manifest": str(output_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
