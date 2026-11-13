from pathlib import Path
import sys
from PIL import Image, ImageDraw

variant = sys.argv[1] if len(sys.argv) > 1 else "initial"
src = Path(__file__).resolve().parents[1] / "build" / f"render-{variant}"
dst = Path(__file__).resolve().parents[1] / "build" / f"contact-{variant}"
dst.mkdir(parents=True, exist_ok=True)
files = sorted(
    [*src.glob("page-*.jpg"), *src.glob("page-*.png")],
    key=lambda p: int(p.stem.split("-")[-1]),
)

cols, rows = 3, 2
thumb_w, thumb_h = 310, 438
label_h = 28
for offset in range(0, len(files), cols * rows):
    group = files[offset : offset + cols * rows]
    sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + label_h)), "#d9d9d9")
    draw = ImageDraw.Draw(sheet)
    for i, path in enumerate(group):
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb_w - 10, thumb_h - 10))
        x = (i % cols) * thumb_w + (thumb_w - image.width) // 2
        y = (i // cols) * (thumb_h + label_h) + 5
        sheet.paste(image, (x, y))
        page_no = int(path.stem.split("-")[-1])
        draw.text(((i % cols) * thumb_w + 10, y + thumb_h), f"Trang PDF {page_no}", fill="black")
    sheet.save(dst / f"contact-{offset // (cols * rows) + 1:02d}.jpg", quality=90)

print(f"Created {len(list(dst.glob('contact-*.jpg')))} contact sheets")
