from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


PROJECT_DIR = Path(__file__).resolve().parents[2]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from backend.scripts.audit_dataset import IMAGE_SUFFIXES, SPLIT_NAMES, resolve_data_root


SPLIT_PRIORITY = {"test": 0, "validate": 1, "validation": 1, "val": 1, "train": 2}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Tạo manifest split sạch, không sửa hoặc sao chép dataset gốc."
    )
    parser.add_argument("dataset", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    data_root = resolve_data_root(args.dataset.resolve())
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    records = []
    for split_dir in sorted(data_root.iterdir()):
        if not split_dir.is_dir() or split_dir.name.casefold() not in SPLIT_NAMES:
            continue
        for class_dir in sorted(item for item in split_dir.iterdir() if item.is_dir()):
            for image in sorted(class_dir.rglob("*")):
                if image.is_file() and image.suffix.lower() in IMAGE_SUFFIXES:
                    records.append(
                        {
                            "split": split_dir.name,
                            "label": class_dir.name,
                            "source_path": str(image),
                            "path": image,
                            "size": image.stat().st_size,
                            "sha256": "",
                        }
                    )

    by_size: dict[int, list[dict[str, object]]] = {}
    for record in records:
        by_size.setdefault(int(record["size"]), []).append(record)

    kept = []
    excluded = []
    duplicate_groups = 0
    conflicting_groups = 0
    for same_size in by_size.values():
        if len(same_size) == 1:
            kept.append(same_size[0])
            continue

        by_hash: dict[str, list[dict[str, object]]] = {}
        for record in same_size:
            digest = sha256_file(record["path"])
            record["sha256"] = digest
            by_hash.setdefault(digest, []).append(record)

        for same_hash in by_hash.values():
            if len(same_hash) == 1:
                kept.append(same_hash[0])
                continue
            duplicate_groups += 1
            labels = {str(record["label"]) for record in same_hash}
            if len(labels) > 1:
                conflicting_groups += 1
                for record in same_hash:
                    record["reason"] = "conflicting_label_duplicate"
                    excluded.append(record)
                continue

            same_hash.sort(
                key=lambda record: (
                    SPLIT_PRIORITY.get(str(record["split"]).casefold(), 99),
                    str(record["source_path"]).casefold(),
                )
            )
            kept.append(same_hash[0])
            for record in same_hash[1:]:
                record["reason"] = "exact_duplicate"
                excluded.append(record)

    fieldnames = ["source_path", "label", "split", "size", "sha256"]
    split_counts = Counter()
    for split in sorted({str(record["split"]) for record in kept}):
        split_records = sorted(
            (record for record in kept if record["split"] == split),
            key=lambda record: (str(record["label"]), str(record["source_path"])),
        )
        split_counts[split] = len(split_records)
        with (output / f"{split.casefold()}.csv").open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(split_records)

    with (output / "excluded_duplicates.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames + ["reason"], extrasaction="ignore")
        writer.writeheader()
        writer.writerows(sorted(excluded, key=lambda record: str(record["source_path"])))

    summary = {
        "sourceDataRoot": str(data_root),
        "policy": (
            "Exact duplicate groups keep one label-consistent file. Cross-split duplicates prefer "
            "Test, then Validate, then Train so evaluation images are removed from training. "
            "Conflicting-label duplicate groups are excluded entirely. Raw data is unchanged."
        ),
        "inputImageCount": len(records),
        "cleanImageCount": len(kept),
        "excludedImageCount": len(excluded),
        "duplicateGroupCount": duplicate_groups,
        "conflictingLabelGroupCount": conflicting_groups,
        "splitImageCounts": dict(sorted(split_counts.items())),
        "classCount": len({str(record["label"]) for record in kept}),
    }
    (output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
