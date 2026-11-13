from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class Figure:
    number: int
    slug: str
    title: str
    group: str
    source: str
    kind: str


FIGURES = (
    Figure(1, "use-case", "Use Case tổng thể", "so-do", "figs/diagrams/use-case.tex", "diagram"),
    Figure(2, "activity-recognition", "Activity nhận diện món ăn", "so-do", "figs/diagrams/activity-recognition.tex", "diagram"),
    Figure(3, "system-architecture", "Kiến trúc hệ thống", "so-do", "figs/diagrams/system-architecture.tex", "diagram"),
    Figure(4, "post-predict-sequence", "Sequence POST /predict", "so-do", "figs/diagrams/recognition-sequence.tex", "diagram"),
    Figure(5, "erd-database", "ERD chín bảng", "so-do", "figs/diagrams/database-erd.tex", "diagram"),
    Figure(6, "vit-pipeline", "Pipeline ViT-L/16", "so-do", "figs/diagrams/vit-pipeline.tex", "diagram"),
    Figure(7, "dataset-splits", "Phân bố Train/Validate/Test", "bieu-do", "figs/charts/dataset-splits.png", "raster"),
    Figure(8, "dataset-classes", "Số ảnh theo 30 lớp", "bieu-do", "figs/charts/dataset-classes.png", "raster"),
    Figure(9, "per-class-f1", "F1 theo từng lớp", "bieu-do", "figs/charts/per-class-metrics.png", "raster"),
    Figure(10, "confusion-matrix", "Ma trận nhầm lẫn chuẩn hóa", "bieu-do", "figs/charts/confusion-matrix.png", "raster"),
    Figure(11, "login", "Màn hình đăng nhập", "giao-dien", "figs/ui/login.png", "raster"),
    Figure(12, "home", "Trang chủ", "giao-dien", "figs/ui/home.png", "raster"),
    Figure(13, "recipes", "Danh mục công thức", "giao-dien", "figs/ui/recipes.png", "raster"),
    Figure(14, "ai-camera-pho", "Camera nhận diện Phở", "giao-dien", "figs/ui/ai-camera-pho.png", "raster"),
    Figure(15, "ai-result-pho", "Kết quả AI Top 1 Phở", "giao-dien", "figs/ui/ai-result-pho.png", "raster"),
    Figure(16, "recipe-license", "Chi tiết nguồn và bản quyền", "giao-dien", "figs/ui/recipe-license.png", "raster"),
)


def run(command: list[str], cwd: Path) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"Lệnh thất bại ({completed.returncode}): {' '.join(command)}\n{completed.stdout}")
    return completed.stdout


def remove_tree_with_retry(path: Path) -> None:
    """MiKTeX đôi khi giữ file log thêm một nhịp trên Windows."""
    for attempt in range(10):
        try:
            shutil.rmtree(path)
            return
        except PermissionError:
            if attempt == 9:
                raise
            time.sleep(0.5)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def diagram_wrapper(report: Path, figure: Figure) -> str:
    font_dir = (report / "styles/fonts").as_posix() + "/"
    theme = (report / "styles/diagram-theme.tex").as_posix()
    source = (report / figure.source).as_posix()
    return rf"""\documentclass[tikz,border=7pt]{{standalone}}
\usepackage{{fontspec}}
\setmainfont{{arial.ttf}}[Path={font_dir},BoldFont=arialbd.ttf,ItalicFont=ariali.ttf,BoldItalicFont=arialbi.ttf]
\usepackage[dvipsnames]{{xcolor}}
\definecolor{{daumaroon}}{{HTML}}{{990000}}
\definecolor{{daugold}}{{HTML}}{{FBAE40}}
\definecolor{{daunavy}}{{HTML}}{{0E2841}}
\definecolor{{agentragreen}}{{HTML}}{{196B24}}
\definecolor{{charcoal}}{{HTML}}{{0E2841}}
\definecolor{{gray700}}{{HTML}}{{384152}}
\definecolor{{gray500}}{{HTML}}{{6B7280}}
\definecolor{{gray300}}{{HTML}}{{DADEE2}}
\definecolor{{gray100}}{{HTML}}{{F3F4F6}}
\definecolor{{lightforest}}{{HTML}}{{E8F0EA}}
\definecolor{{lightwarm}}{{HTML}}{{FCEFD9}}
\definecolor{{lightnavy}}{{HTML}}{{E7EBF0}}
\usetikzlibrary{{shapes.geometric,arrows.meta,positioning,calc,fit,shadows}}
\input{{{theme}}}
\begin{{document}}
\input{{{source}}}
\end{{document}}
"""


def export_diagram(report: Path, temp: Path, output: Path, figure: Figure) -> tuple[Path, Path]:
    xelatex = shutil.which("xelatex")
    pdftoppm = shutil.which("pdftoppm")
    if not xelatex or not pdftoppm:
        raise RuntimeError("Cần có xelatex và pdftoppm trong PATH để xuất sơ đồ.")
    basename = f"{figure.number:02d}-{figure.slug}"
    work = temp / basename
    work.mkdir(parents=True, exist_ok=True)
    wrapper = work / "figure.tex"
    wrapper.write_text(diagram_wrapper(report, figure), encoding="utf-8")
    run([xelatex, "-disable-installer", "-interaction=nonstopmode", "-halt-on-error", "figure.tex"], work)
    pdf_target = output / figure.group / f"{basename}.pdf"
    png_target = output / figure.group / f"{basename}.png"
    shutil.copy2(work / "figure.pdf", pdf_target)
    render_stem = work / "rendered"
    run([pdftoppm, "-png", "-r", "300", "-singlefile", str(work / "figure.pdf"), str(render_stem)], work)
    shutil.copy2(work / "rendered.png", png_target)
    return png_target, pdf_target


def raster_pdf(source: Path, target: Path) -> None:
    with Image.open(source) as image:
        rgb = image.convert("RGB")
        rgb.save(target, "PDF", resolution=150.0, quality=95)


def export_raster(report: Path, output: Path, figure: Figure) -> tuple[Path, Path]:
    source = report / figure.source
    basename = f"{figure.number:02d}-{figure.slug}"
    png_target = output / figure.group / f"{basename}.png"
    pdf_target = output / figure.group / f"{basename}.pdf"
    shutil.copy2(source, png_target)
    raster_pdf(source, pdf_target)
    return png_target, pdf_target


def pdf_dimensions(path: Path) -> str:
    pdfinfo = shutil.which("pdfinfo")
    if not pdfinfo:
        return "1 trang"
    output = run([pdfinfo, str(path)], path.parent)
    match = re.search(r"^Page size:\s+(.+)$", output, flags=re.MULTILINE)
    return match.group(1).strip() if match else "1 trang"


def manifest_row(report: Path, figure: Figure, path: Path) -> dict[str, str | int]:
    if path.suffix.lower() == ".png":
        with Image.open(path) as image:
            dimensions = f"{image.width}x{image.height} px"
    else:
        dimensions = pdf_dimensions(path)
    return {
        "figure_number": figure.number,
        "title": figure.title,
        "group": figure.group,
        "format": path.suffix.lower().lstrip("."),
        "dimensions": dimensions,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "source_file": figure.source.replace("/", "\\"),
    }


def write_readme(output: Path) -> None:
    (output / "README.md").write_text(
        """# Bộ hình ảnh báo cáo Vị Việt

Thư mục này là bản xuất độc lập để xem hoặc chèn vào Word/PowerPoint. Báo
cáo LaTeX không phụ thuộc vào thư mục này.

- `so-do/`: 6 sơ đồ, PDF vector từ TikZ và PNG render 300 DPI.
- `bieu-do/`: 4 biểu đồ PNG độ phân giải cao và PDF một trang.
- `giao-dien/`: 6 ảnh giao diện PNG và PDF một trang.
- `manifest.csv`: số hình, nhóm, định dạng, kích thước, dung lượng, SHA-256
  và file nguồn nội bộ của báo cáo.

Chạy lại `tools\\export_images.bat` trong thư mục báo cáo để tái tạo bộ hình.
""",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Xuất 16 hình của báo cáo sang thư mục độc lập.")
    parser.add_argument("--report", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path("D:/BaoCaoViViet-HinhAnh"))
    args = parser.parse_args()
    report = args.report.resolve()
    output = args.output.resolve()
    temp_root = report / "build/figure-export"
    temp_root.mkdir(parents=True, exist_ok=True)
    temp = temp_root / f"run-{os.getpid()}"
    temp.mkdir(parents=True)
    for group in ("so-do", "bieu-do", "giao-dien"):
        (output / group).mkdir(parents=True, exist_ok=True)

    for figure in FIGURES:
        basename = f"{figure.number:02d}-{figure.slug}"
        for suffix in (".png", ".pdf"):
            target = output / figure.group / f"{basename}{suffix}"
            if target.exists():
                target.unlink()

    rows: list[dict[str, str | int]] = []
    for figure in FIGURES:
        exported = (
            export_diagram(report, temp, output, figure)
            if figure.kind == "diagram"
            else export_raster(report, output, figure)
        )
        rows.extend(manifest_row(report, figure, path) for path in exported)

    fieldnames = ["figure_number", "title", "group", "format", "dimensions", "bytes", "sha256", "source_file"]
    with (output / "manifest.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    write_readme(output)
    try:
        remove_tree_with_retry(temp)
    except PermissionError:
        # File tạm vẫn nằm đúng build/figure-export và sẽ được dọn ở lần sau.
        pass
    print(f"Exported {len(FIGURES)} figures and {len(rows)} PNG/PDF files to {output}")


if __name__ == "__main__":
    main()
