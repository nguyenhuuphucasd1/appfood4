from __future__ import annotations

import sys
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


PROJECT_DIR = Path(__file__).resolve().parents[2]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from transformers import AutoImageProcessor, AutoModelForImageClassification

from backend.ai.model_loader import has_complete_local_model
from backend.config import MODEL_DIR, MODEL_NAME


def main() -> int:
    if has_complete_local_model(MODEL_DIR):
        print(f"Model đã tồn tại đầy đủ tại: {MODEL_DIR}")
        return 0

    print(f"Đang tải model {MODEL_NAME}...")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    try:
        processor = AutoImageProcessor.from_pretrained(MODEL_NAME)
        model = AutoModelForImageClassification.from_pretrained(MODEL_NAME)
        processor.save_pretrained(MODEL_DIR)
        model.save_pretrained(MODEL_DIR, safe_serialization=True)
    except Exception as exc:
        print(f"Tải model thất bại: {exc}", file=sys.stderr)
        return 1

    if not has_complete_local_model(MODEL_DIR):
        print("Model tải xong nhưng thiếu config/processor/trọng số.", file=sys.stderr)
        return 1

    print(f"Đã lưu model tại: {MODEL_DIR}")
    for path in sorted(MODEL_DIR.iterdir()):
        if path.is_file():
            print(f"- {path.name}: {path.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
