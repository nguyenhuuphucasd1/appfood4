from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


PROJECT_DIR = Path(__file__).resolve().parents[2]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from backend.ai.predictor import predict_image
from backend.recipes.normalizer import normalize_dish_name
from backend.scripts.audit_dataset import discover_classes, resolve_data_root


def main() -> int:
    parser = argparse.ArgumentParser(description="Đánh giá mẫu, không suy diễn accuracy tổng thể.")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--per-class", type=int, default=1)
    parser.add_argument("--split", default="Test", help="Tên split cần đánh giá, mặc định Test")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    root = args.dataset.resolve()
    if not root.is_dir():
        print(f"Không tìm thấy dataset: {root}", file=sys.stderr)
        return 2
    data_root = resolve_data_root(root)
    evaluation_root = data_root
    if args.split:
        split = next(
            (
                item
                for item in data_root.iterdir()
                if item.is_dir() and item.name.casefold() == args.split.casefold()
            ),
            None,
        )
        if split is None:
            available = ", ".join(sorted(item.name for item in data_root.iterdir() if item.is_dir()))
            print(f"Không tìm thấy split '{args.split}'. Hiện có: {available}", file=sys.stderr)
            return 4
        evaluation_root = split

    classes, _ = discover_classes(evaluation_root)
    if not classes:
        print("Không tìm thấy thư mục class chứa ảnh món ăn có nhãn.", file=sys.stderr)
        return 3

    rows = []
    for ground_truth, images in sorted(classes.items()):
        for image_path in images[: args.per_class]:
            result = predict_image(image_path.read_bytes())
            prediction = result["prediction"]
            correct = normalize_dish_name(ground_truth) == normalize_dish_name(prediction["dish"])
            rows.append(
                {
                    "image": str(image_path),
                    "ground_truth": ground_truth,
                    "prediction": prediction["dish"],
                    "confidence": prediction["confidence"],
                    "correct": correct,
                }
            )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
    writer_target = args.output.open("w", newline="", encoding="utf-8-sig") if args.output else sys.stdout
    try:
        writer = csv.DictWriter(writer_target, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    finally:
        if args.output:
            writer_target.close()
    print(f"Đã kiểm tra {len(rows)} ảnh mẫu; đây không phải accuracy toàn bộ dataset.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
