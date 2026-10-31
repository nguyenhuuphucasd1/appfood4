from __future__ import annotations

import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import Dish


DISH_NAMES = (
    "Bánh cuốn", "Mì Quảng", "Bánh tráng nướng", "Gỏi cuốn", "Bánh giò",
    "Bún mắm", "Canh chua", "Nem chua", "Bún riêu", "Bánh đúc", "Bánh pía",
    "Bánh canh", "Bánh khọt", "Bánh bột lọc", "Bánh căn", "Bún thịt nướng",
    "Bánh chưng", "Bún đậu mắm tôm", "Bánh bèo", "Bánh tét", "Cao lầu",
    "Cháo lòng", "Cá kho tộ", "Bún bò Huế", "Phở", "Xôi xéo", "Bánh mì",
    "Bánh xèo", "Cơm tấm", "Hủ tiếu", "Bánh cu đơ", "Nem nướng",
    "Bánh mì cay", "Cơm cháy", "Bò bía", "Bánh đậu xanh", "Bánh đa cua", "Bún cá",
)


def normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.casefold().replace("đ", "d"))
    without_marks = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return " ".join(without_marks.split())


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", normalize_text(value)).strip("-")


def seed_catalog(db: Session) -> None:
    existing = set(db.scalars(select(Dish.slug)).all())
    for name in DISH_NAMES:
        slug = slugify(name)
        if slug not in existing:
            db.add(Dish(slug=slug, name=name, normalized_name=normalize_text(name)))
    db.commit()
