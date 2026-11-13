from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader


def main() -> int:
    pdf_path = Path(sys.argv[1]).resolve()
    reader = PdfReader(pdf_path)
    page_texts = [(page.extract_text() or "") for page in reader.pages]
    text = "\n".join(page_texts)

    forbidden = [
        "CHƯA HOÀN TẤT",
        "NỘI DUNG MẪU",
        "??",
        "KGAT_",
        "@gmail.com",
        "kaggle.json",
        "\ufffd",
    ]
    issues = [value for value in forbidden if value in text]
    short_pages = [
        index + 1
        for index, value in enumerate(page_texts)
        if len(re.sub(r"\s+", "", value)) < 30
    ]
    expected = ["5.014", "4.690", "93,54%", "93,68%"]
    missing_expected = [value for value in expected if value not in text]
    result = {
        "file": str(pdf_path),
        "pages": len(reader.pages),
        "forbidden_matches": issues,
        "short_pages": short_pages,
        "missing_expected_metrics": missing_expected,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if issues or short_pages or missing_expected else 0


if __name__ == "__main__":
    raise SystemExit(main())
