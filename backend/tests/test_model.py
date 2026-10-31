from __future__ import annotations

import argparse
import sys
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


PROJECT_DIR = Path(__file__).resolve().parents[2]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from backend.ai.model_loader import get_model_bundle
from backend.ai.predictor import predict_image


def main() -> int:
    parser = argparse.ArgumentParser(description="Test độc lập pretrained food classifier.")
    parser.add_argument("image", type=Path)
    args = parser.parse_args()
    if not args.image.is_file():
        print(f"Không tìm thấy ảnh: {args.image}", file=sys.stderr)
        return 2

    bundle = get_model_bundle()
    result = predict_image(args.image.read_bytes(), bundle=bundle)
    prediction = result["prediction"]
    print(f"Device: {bundle.device.type.upper()}")
    print("\nPrediction:")
    print(f"Tên món: {prediction['dish']}")
    print(f"Confidence: {prediction['confidence'] * 100:.2f}%")
    print(f"Accepted: {prediction['accepted']}")
    print("\nTop 3:")
    for index, item in enumerate(result["top3"], start=1):
        print(f"{index}. {item['dish']} - {item['confidence'] * 100:.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
