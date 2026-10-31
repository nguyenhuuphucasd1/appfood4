from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path


ALIASES_PATH = Path(__file__).with_name("aliases.json")


def _key(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value).casefold()
    normalized = re.sub(r"[_-]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def load_aliases(path: Path = ALIASES_PATH) -> dict[str, str]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    return {_key(alias): str(canonical) for alias, canonical in raw.items()}


def normalize_dish_name(value: str, aliases: dict[str, str] | None = None) -> str:
    """Normalize formatting, then apply only explicitly sourced aliases."""
    lookup = aliases if aliases is not None else load_aliases()
    normalized = _key(value)
    return lookup.get(normalized, normalized)

