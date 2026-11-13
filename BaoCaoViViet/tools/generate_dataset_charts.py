from __future__ import annotations

import csv
import json
import sqlite3
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


GREEN = "#1F7A3F"
DARK = "#142218"
ORANGE = "#F26A2E"
CREAM = "#FFF9F0"
MUTED = "#6D776F"


def font(size: int, bold: bool = False):
    name = "arialbd.ttf" if bold else "arial.ttf"
    path = Path("C:/Windows/Fonts") / name
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def split_chart(summary_path: Path, output: Path) -> None:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    counts = summary["splitImageCounts"]
    split_keys = ["Train", "Validate", "Test"]
    labels = ["Huấn luyện", "Xác thực", "Kiểm thử"]
    values = [counts[label] for label in split_keys]
    image = Image.new("RGB", (1800, 1050), CREAM)
    draw = ImageDraw.Draw(image)
    draw.text((90, 55), "Phân bố tập dữ liệu sạch 30VNFoods", fill=DARK, font=font(54, True))
    max_value = max(values)
    colors = [GREEN, ORANGE, "#12552B"]
    base_y = 860
    for index, (label, value) in enumerate(zip(labels, values, strict=True)):
        x0 = 180 + index * 520
        height = int(600 * value / max_value)
        draw.rounded_rectangle((x0, base_y - height, x0 + 300, base_y), radius=25, fill=colors[index])
        draw.text((x0 + 150, base_y - height - 70), f"{value:,}".replace(",", "."), anchor="mm", fill=DARK, font=font(42, True))
        draw.text((x0 + 150, base_y + 50), label, anchor="mm", fill=DARK, font=font(38))
    draw.text((90, 980), f"Tổng: {summary['cleanImageCount']:,} ảnh | Loại: {summary['excludedImageCount']} ảnh trùng/mâu thuẫn".replace(",", "."), fill=MUTED, font=font(30))
    image.save(output, quality=95)


def load_display_names(project: Path) -> dict[str, str]:
    with sqlite3.connect(project / "backend/data/vi_viet.db") as connection:
        return {
            str(normalized).casefold(): str(name)
            for normalized, name in connection.execute(
                "SELECT normalized_name, name FROM dishes ORDER BY id"
            )
        }


def class_chart(manifest_dir: Path, project: Path, output: Path) -> None:
    counts: Counter[str] = Counter()
    for filename in ("train.csv", "validate.csv", "test.csv"):
        with (manifest_dir / filename).open(encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream):
                counts[row["label"]] += 1
    display_names = load_display_names(project)
    rows = sorted(counts.items(), key=lambda item: (item[1], item[0]))
    image = Image.new("RGB", (3200, 1850), "white")
    draw = ImageDraw.Draw(image)
    draw.text((80, 45), "Số ảnh sạch theo 30 lớp", fill=DARK, font=font(52, True))
    max_value = max(counts.values())
    top = 180
    row_height = 104
    for index, (label, value) in enumerate(rows):
        column = index // 15
        row = index % 15
        panel_x = 80 + column * 1580
        y = top + row * row_height
        display_label = display_names.get(label.casefold(), label)
        draw.text((panel_x, y + 32), display_label, anchor="lm", fill=DARK, font=font(30))
        x0 = panel_x + 480
        width = int(900 * value / max_value)
        draw.rounded_rectangle((x0, y + 8, x0 + width, y + 58), radius=14, fill=GREEN)
        draw.text((x0 + width + 22, y + 33), str(value), anchor="lm", fill=MUTED, font=font(27, True))
    image.save(output, quality=95)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    project = Path("D:/appfood4")
    manifest_dir = project / "datasets/processed/30VNFoods_clean/manifests"
    charts = root / "figs/charts"
    charts.mkdir(parents=True, exist_ok=True)
    split_chart(manifest_dir / "summary.json", charts / "dataset-splits.png")
    class_chart(manifest_dir, project, charts / "dataset-classes.png")
    print(f"Created charts in {charts}")


if __name__ == "__main__":
    main()
