from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


PROJECT_DIR = Path(__file__).resolve().parents[2]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from backend.scripts.audit_dataset import discover_classes, resolve_data_root


def label_key(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


def main() -> int:
    parser = argparse.ArgumentParser(description="Đối chiếu nhãn dataset với nhãn model mà không tự đoán alias.")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("model_config", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    data_root = resolve_data_root(args.dataset.resolve())
    classes, _ = discover_classes(data_root)
    if not classes:
        print("Không tìm thấy nhãn dataset.", file=sys.stderr)
        return 2

    config = json.loads(args.model_config.read_text(encoding="utf-8"))
    id2label = config.get("id2label", {})
    model_labels = [str(label) for _, label in sorted(id2label.items(), key=lambda item: int(item[0]))]
    model_by_key: dict[str, list[str]] = {}
    for label in model_labels:
        model_by_key.setdefault(label_key(label), []).append(label)

    mappings = []
    unmatched = []
    ambiguous = []
    for dataset_label in sorted(classes):
        candidates = model_by_key.get(label_key(dataset_label), [])
        if len(candidates) == 1:
            mappings.append(
                {
                    "datasetLabel": dataset_label,
                    "modelLabel": candidates[0],
                    "match": "exact" if dataset_label == candidates[0] else "normalized",
                }
            )
        elif not candidates:
            unmatched.append(dataset_label)
        else:
            ambiguous.append({"datasetLabel": dataset_label, "modelLabels": candidates})

    matched_model_labels = {item["modelLabel"] for item in mappings}
    report = {
        "datasetClassCount": len(classes),
        "modelClassCount": len(model_labels),
        "matchedCount": len(mappings),
        "unmatchedDatasetLabels": unmatched,
        "ambiguousMappings": ambiguous,
        "modelOnlyLabels": [label for label in model_labels if label not in matched_model_labels],
        "mappings": mappings,
        "policy": "Only exact or Unicode/case/whitespace-normalized matches are accepted; no aliases are inferred.",
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if not unmatched and not ambiguous else 3


if __name__ == "__main__":
    raise SystemExit(main())
