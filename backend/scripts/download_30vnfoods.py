from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[2]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from backend.scripts.managed_paths import RAW_DATASETS_DIR, configure_storage_environment, require_kaggle_token


DEFAULT_DATASET_REF = "quandang/vietnamese-foods"


def main() -> int:
    parser = argparse.ArgumentParser(description="Tai 30VNFoods vao o D cua du an.")
    parser.add_argument("--dataset", default=DEFAULT_DATASET_REF, help="Kaggle dataset reference")
    parser.add_argument("--output", type=Path, default=RAW_DATASETS_DIR / "30VNFoods")
    parser.add_argument("--resume", action="store_true", help="Cho phep dung thu muc output da co du lieu")
    args = parser.parse_args()

    configure_storage_environment()
    try:
        require_kaggle_token()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 4
    target = args.output.resolve()
    raw_root = RAW_DATASETS_DIR.resolve()
    if raw_root not in target.parents and target != raw_root:
        print(f"Output phai nam trong {raw_root}", file=sys.stderr)
        return 2
    if target.exists() and any(target.iterdir()) and not args.resume:
        print(f"Thu muc da co du lieu: {target}. Dung --resume neu muon tiep tuc.", file=sys.stderr)
        return 3
    target.mkdir(parents=True, exist_ok=True)

    try:
        # Kaggle 1.8+ authenticates at import time from access_token or
        # kaggle.json. Reusing that client avoids authenticating twice.
        import kaggle

        kaggle.api.dataset_download_files(args.dataset, path=str(target), unzip=True, quiet=False)
    except Exception as exc:
        print(f"Tai dataset that bai: {exc}", file=sys.stderr)
        return 1

    manifest = {
        "dataset": args.dataset,
        "downloadedAt": datetime.now(UTC).isoformat(),
        "path": str(target),
        "files": sum(1 for item in target.rglob("*") if item.is_file()),
    }
    (target / "download_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
