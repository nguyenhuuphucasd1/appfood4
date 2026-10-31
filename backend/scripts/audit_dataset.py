from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from PIL import Image


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
SPLIT_NAMES = {"train", "test", "val", "valid", "validate", "validation"}
NON_DATA_DIRS = {"google sheets", "model implement", ".git", "__pycache__"}


def images_below(path: Path) -> list[Path]:
    return sorted(
        item
        for item in path.rglob("*")
        if item.is_file() and item.suffix.lower() in IMAGE_SUFFIXES
    )


def resolve_data_root(root: Path) -> Path:
    """Return the folder that directly contains split or class folders."""
    candidates = [root, root / "Images", root / "images"]
    for candidate in candidates:
        if not candidate.is_dir():
            continue
        if any(
            item.is_dir() and item.name.casefold() in SPLIT_NAMES
            for item in candidate.iterdir()
        ):
            return candidate
    return root


def discover_classes(root: Path) -> tuple[dict[str, list[Path]], dict[str, dict[str, list[Path]]]]:
    split_dirs = [item for item in root.iterdir() if item.is_dir() and item.name.casefold() in SPLIT_NAMES]
    containers = split_dirs or [root]
    classes: dict[str, list[Path]] = {}
    splits: dict[str, dict[str, list[Path]]] = {}
    for container in containers:
        split_name = container.name if split_dirs else "all"
        split_classes: dict[str, list[Path]] = {}
        for class_dir in container.iterdir():
            if not class_dir.is_dir() or class_dir.name.casefold() in NON_DATA_DIRS:
                continue
            found = images_below(class_dir)
            if found:
                classes.setdefault(class_dir.name, []).extend(found)
                split_classes[class_dir.name] = found
        if split_classes:
            splits[split_name] = split_classes
    return classes, splits


def verify_images(images: list[Path]) -> tuple[int, list[dict[str, str]]]:
    invalid: list[dict[str, str]] = []
    for path in images:
        try:
            with Image.open(path) as image:
                image.verify()
        except Exception as exc:  # Pillow raises several format-specific exceptions.
            invalid.append({"path": str(path), "error": str(exc)})
    return len(invalid), invalid[:50]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_duplicates(images: list[Path], data_root: Path) -> dict[str, object]:
    by_size: dict[int, list[Path]] = {}
    for path in images:
        by_size.setdefault(path.stat().st_size, []).append(path)

    by_hash: dict[str, list[Path]] = {}
    for same_size in by_size.values():
        if len(same_size) < 2:
            continue
        for path in same_size:
            by_hash.setdefault(sha256_file(path), []).append(path)

    groups = [paths for paths in by_hash.values() if len(paths) > 1]
    cross_split_groups = []
    conflicting_label_groups = []
    for paths in groups:
        relative_parts = [path.relative_to(data_root).parts for path in paths]
        split_names = {parts[0] for parts in relative_parts if parts}
        label_names = {parts[1] for parts in relative_parts if len(parts) > 1}
        if len(split_names) > 1:
            cross_split_groups.append(paths)
        if len(label_names) > 1:
            conflicting_label_groups.append(paths)

    return {
        "groupCount": len(groups),
        "duplicateFileCount": sum(len(paths) - 1 for paths in groups),
        "crossSplitGroupCount": len(cross_split_groups),
        "conflictingLabelGroupCount": len(conflicting_label_groups),
        "examples": [[str(path) for path in paths] for paths in groups[:50]],
        "crossSplitExamples": [
            [str(path) for path in paths] for paths in cross_split_groups[:50]
        ],
        "conflictingLabelExamples": [
            [str(path) for path in paths] for paths in conflicting_label_groups[:50]
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Kiểm tra cấu trúc dataset ảnh có nhãn.")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--json", action="store_true", help="In kết quả JSON")
    parser.add_argument("--output", type=Path, help="Lưu báo cáo JSON vào file")
    parser.add_argument("--verify-images", action="store_true", help="Dùng Pillow kiểm tra ảnh hỏng")
    parser.add_argument("--find-duplicates", action="store_true", help="Tìm file ảnh trùng SHA-256")
    args = parser.parse_args()
    source_root = args.dataset.resolve()
    if not source_root.is_dir():
        print(f"Không tìm thấy dataset: {source_root}")
        return 2

    root = resolve_data_root(source_root)
    classes, splits = discover_classes(root)
    images = [path for paths in classes.values() for path in paths]
    report = {
        "sourceRoot": str(source_root),
        "dataRoot": str(root),
        "classCount": len(classes),
        "classes": sorted(classes),
        "imageCount": len(images),
        "formats": dict(sorted(Counter(path.suffix.lower() for path in images).items())),
        "splits": {
            split: {
                "classCount": len(split_classes),
                "imageCount": sum(len(paths) for paths in split_classes.values()),
                "classImageCounts": {
                    name: len(paths) for name, paths in sorted(split_classes.items())
                },
            }
            for split, split_classes in sorted(splits.items())
        },
        "samples": [str(paths[0]) for _, paths in sorted(classes.items()) if paths],
    }
    if args.verify_images:
        invalid_count, invalid_examples = verify_images(images)
        report["imageValidation"] = {
            "checked": len(images),
            "invalidCount": invalid_count,
            "invalidExamples": invalid_examples,
        }
    if args.find_duplicates:
        report["duplicates"] = find_duplicates(images, root)

    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    if args.json:
        print(rendered)
    else:
        print(f"Dataset: {report['dataRoot']}")
        print(f"Số class: {report['classCount']}")
        print(f"Số ảnh có nhãn: {report['imageCount']}")
        print("Class: " + (", ".join(report["classes"]) or "không tìm thấy"))
        print(f"Định dạng: {report['formats']}")
    return 0 if classes else 3


if __name__ == "__main__":
    raise SystemExit(main())
