from __future__ import annotations

import argparse
import csv
import json
import math
import sqlite3
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import torch
from PIL import Image, ImageDraw, ImageFont
from transformers import AutoImageProcessor, AutoModelForImageClassification


FIELDNAMES = [
    "source_path", "ground_truth", "ground_truth_canonical", "prediction",
    "prediction_canonical", "confidence", "correct", "inference_ms",
]
GREEN = "#1F7A3F"
DARK_GREEN = "#12552B"
ORANGE = "#F26A2E"
DARK = "#142218"
MUTED = "#6D776F"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def get_font(size: int, bold: bool = False):
    name = "arialbd.ttf" if bold else "arial.ttf"
    path = Path("C:/Windows/Fonts") / name
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise RuntimeError(f"Manifest is empty: {path}")
    return rows


def read_existing(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return {row["source_path"]: row for row in csv.DictReader(stream)}


def append_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    create_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDNAMES)
        if create_header:
            writer.writeheader()
        writer.writerows(rows)


def load_rgb(paths: list[Path]) -> list[Image.Image]:
    images: list[Image.Image] = []
    for path in paths:
        with Image.open(path) as source:
            images.append(source.convert("RGB"))
    return images


def run_predictions(args, normalize_dish_name) -> None:
    manifest_rows = read_manifest(args.manifest)
    completed = read_existing(args.output)
    pending = [row for row in manifest_rows if row["source_path"] not in completed]
    print(f"Manifest: {len(manifest_rows)} | completed: {len(completed)} | pending: {len(pending)}")
    if not pending:
        return

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    processor = AutoImageProcessor.from_pretrained(args.model, local_files_only=True)
    model = AutoModelForImageClassification.from_pretrained(args.model, local_files_only=True)
    model.to(device)
    model.eval()
    batch_size = max(1, args.batch_size)
    index = 0
    started = time.perf_counter()
    while index < len(pending):
        batch = pending[index:index + batch_size]
        paths = [Path(row["source_path"]) for row in batch]
        try:
            images = load_rgb(paths)
            tick = time.perf_counter()
            inputs = processor(images=images, return_tensors="pt")
            inputs = {key: value.to(device) for key, value in inputs.items()}
            with torch.inference_mode():
                logits = model(**inputs).logits
                probabilities = torch.softmax(logits, dim=-1)
                scores, indices = torch.max(probabilities, dim=-1)
            elapsed_ms = (time.perf_counter() - tick) * 1000.0 / len(batch)
        except RuntimeError as exc:
            if "out of memory" in str(exc).lower() and batch_size > 1:
                batch_size = max(1, batch_size // 2)
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                print(f"Out of memory; retrying with batch_size={batch_size}", file=sys.stderr)
                continue
            raise

        output_rows = []
        for source, score, predicted_index in zip(batch, scores, indices, strict=True):
            raw_prediction = str(model.config.id2label.get(int(predicted_index.item()), predicted_index.item()))
            truth = source["label"]
            truth_canonical = normalize_dish_name(truth)
            prediction_canonical = normalize_dish_name(raw_prediction)
            output_rows.append({
                "source_path": source["source_path"],
                "ground_truth": truth,
                "ground_truth_canonical": truth_canonical,
                "prediction": raw_prediction,
                "prediction_canonical": prediction_canonical,
                "confidence": f"{float(score.item()):.8f}",
                "correct": str(truth_canonical == prediction_canonical).lower(),
                "inference_ms": f"{elapsed_ms:.3f}",
            })
        append_rows(args.output, output_rows)
        index += len(batch)
        done = len(completed) + index
        if done % 100 < len(batch) or done == len(manifest_rows):
            duration = time.perf_counter() - started
            rate = index / duration if duration else 0.0
            print(f"{done}/{len(manifest_rows)} ({done / len(manifest_rows):.1%}) | {rate:.2f} images/s", flush=True)


def load_display_names(project: Path) -> dict[str, str]:
    database = project / "backend/data/vi_viet.db"
    with sqlite3.connect(database) as connection:
        return {
            str(normalized): str(name)
            for normalized, name in connection.execute(
                "SELECT normalized_name, name FROM dishes ORDER BY id"
            )
        }


def calculate_metrics(prediction_path: Path, output_dir: Path, project: Path) -> dict:
    with prediction_path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    unique = {row["source_path"]: row for row in rows}
    rows = list(unique.values())
    display_names = load_display_names(project)
    true_labels = sorted({row["ground_truth_canonical"] for row in rows})
    predicted_labels = sorted({row["prediction_canonical"] for row in rows})
    confusion: Counter[tuple[str, str]] = Counter(
        (row["ground_truth_canonical"], row["prediction_canonical"]) for row in rows
    )
    correct = sum(row["correct"].lower() == "true" for row in rows)
    per_class = []
    for label in true_labels:
        tp = confusion[label, label]
        fp = sum(confusion[truth, label] for truth in true_labels if truth != label)
        fn = sum(count for (truth, prediction), count in confusion.items() if truth == label and prediction != label)
        support = sum(count for (truth, _), count in confusion.items() if truth == label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class.append({
            "label": display_names.get(label, label), "support": support, "tp": tp, "fp": fp, "fn": fn,
            "precision": precision, "recall": recall, "f1": f1,
        })
    timings = [float(row["inference_ms"]) for row in rows]
    confidences = [float(row["confidence"]) for row in rows]
    top_confusions = [
        {
            "ground_truth": display_names.get(truth, truth),
            "prediction": display_names.get(prediction, prediction),
            "count": count,
        }
        for (truth, prediction), count in confusion.most_common()
        if truth != prediction
    ][:20]
    metrics = {
        "sample_count": len(rows),
        "class_count": len(true_labels),
        "correct": correct,
        "accuracy": correct / len(rows),
        "macro_precision": statistics.fmean(item["precision"] for item in per_class),
        "macro_recall": statistics.fmean(item["recall"] for item in per_class),
        "macro_f1": statistics.fmean(item["f1"] for item in per_class),
        "mean_confidence": statistics.fmean(confidences),
        "mean_inference_ms": statistics.fmean(timings),
        "median_inference_ms": statistics.median(timings),
        "p95_inference_ms": percentile(timings, 0.95),
        "true_labels": [display_names.get(label, label) for label in true_labels],
        "predicted_labels": [display_names.get(label, label) for label in predicted_labels],
        "top_confusions": top_confusions,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    with (output_dir / "per-class-metrics.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(per_class[0].keys()))
        writer.writeheader()
        writer.writerows(per_class)
    with (output_dir / "confusion-matrix.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["ground_truth", *[display_names.get(label, label) for label in predicted_labels]])
        for truth in true_labels:
            writer.writerow([display_names.get(truth, truth), *[confusion[truth, pred] for pred in predicted_labels]])
    write_metrics_tex(metrics, output_dir / "metrics.tex")
    write_tables_tex(per_class, top_confusions, output_dir)
    draw_per_class(per_class, output_dir.parent / "figs/charts/per-class-metrics.png")
    draw_confusion(rows, true_labels, display_names, output_dir.parent / "figs/charts/confusion-matrix.png")
    return metrics


def write_metrics_tex(metrics: dict, path: Path) -> None:
    content = "\n".join([
        f"\\newcommand{{\\EvalTotal}}{{{metrics['sample_count']:,}}}".replace(",", "."),
        f"\\newcommand{{\\EvalCorrect}}{{{metrics['correct']:,}}}".replace(",", "."),
        f"\\newcommand{{\\EvalAccuracy}}{{{metrics['accuracy'] * 100:.2f}\\%}}".replace(".", ","),
        f"\\newcommand{{\\EvalMacroPrecision}}{{{metrics['macro_precision'] * 100:.2f}\\%}}".replace(".", ","),
        f"\\newcommand{{\\EvalMacroRecall}}{{{metrics['macro_recall'] * 100:.2f}\\%}}".replace(".", ","),
        f"\\newcommand{{\\EvalMacroFOne}}{{{metrics['macro_f1'] * 100:.2f}\\%}}".replace(".", ","),
        f"\\newcommand{{\\EvalMeanConfidence}}{{{metrics['mean_confidence'] * 100:.2f}\\%}}".replace(".", ","),
        f"\\newcommand{{\\EvalMeanMs}}{{{metrics['mean_inference_ms']:.1f}}}".replace(".", ","),
        f"\\newcommand{{\\EvalPPercentileMs}}{{{metrics['p95_inference_ms']:.1f}}}".replace(".", ","),
        "",
    ])
    path.write_text(content, encoding="utf-8")


def latex_escape(value: str) -> str:
    return value.replace("&", "\\&").replace("_", "\\_").replace("%", "\\%")


def write_tables_tex(per_class: list[dict], top_confusions: list[dict], output_dir: Path) -> None:
    confusion_lines = [
        "\\begin{table}[H]",
        "\\centering",
        "\\caption{Các cặp nhầm lẫn xuất hiện nhiều nhất.}",
        "\\label{tab:top-confusions}",
        "\\begin{tabular}{>{\\bfseries}l l r}",
        "\\toprule Nhãn thật & Dự đoán & Số ảnh \\\\",
        "\\midrule",
    ]
    for item in top_confusions[:10]:
        confusion_lines.append(
            f"{latex_escape(item['ground_truth'])} & {latex_escape(item['prediction'])} & {item['count']} \\\\"
        )
    confusion_lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table}", ""])
    (output_dir / "top-confusions.tex").write_text("\n".join(confusion_lines), encoding="utf-8")

    class_lines = [
        "\\begin{longtable}{>{\\bfseries}p{4.1cm}rrrr}",
        "\\caption{Độ đo theo từng lớp trên tập Test sạch.}\\label{tab:per-class}\\\\",
        "\\toprule Lớp & Support & Precision & Recall & F1 \\\\",
        "\\midrule \\endfirsthead",
        "\\toprule Lớp & Support & Precision & Recall & F1 \\\\",
        "\\midrule \\endhead",
    ]
    for item in sorted(per_class, key=lambda row: row["label"]):
        class_lines.append(
            f"{latex_escape(item['label'])} & {item['support']} & "
            f"{item['precision'] * 100:.2f}\\% & {item['recall'] * 100:.2f}\\% & "
            f"{item['f1'] * 100:.2f}\\% \\\\".replace(".", ",")
        )
    class_lines.extend(["\\bottomrule", "\\end{longtable}", ""])
    (output_dir / "per-class-table.tex").write_text("\n".join(class_lines), encoding="utf-8")


def draw_per_class(per_class: list[dict], path: Path) -> None:
    rows = sorted(per_class, key=lambda item: item["f1"])
    image = Image.new("RGB", (2500, 1400), "white")
    draw = ImageDraw.Draw(image)
    draw.text((80, 45), "F1 theo từng lớp trên tập Test sạch", fill=DARK, font=get_font(52, True))
    top, row_height = 150, 78
    rows_per_column = math.ceil(len(rows) / 2)
    for index, item in enumerate(rows):
        column = index // rows_per_column
        row_index = index % rows_per_column
        base_x = 80 + column * 1210
        y = top + row_index * row_height
        draw.text((base_x, y + 27), item["label"], anchor="lm", fill=DARK, font=get_font(25))
        x0 = base_x + 430
        width = int(650 * item["f1"])
        color = GREEN if item["f1"] >= 0.8 else ORANGE
        draw.rounded_rectangle((x0, y + 6, x0 + width, y + 49), radius=12, fill=color)
        draw.text((x0 + width + 16, y + 28), f"{item['f1'] * 100:.1f}%", anchor="lm", fill=MUTED, font=get_font(23, True))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, quality=95)


def draw_confusion(rows: list[dict], labels: list[str], display_names: dict[str, str], path: Path) -> None:
    label_set = set(labels)
    grouped = labels + ["Ngoài 30 lớp"]
    matrix: Counter[tuple[str, str]] = Counter()
    support: Counter[str] = Counter()
    for row in rows:
        truth = row["ground_truth_canonical"]
        prediction = row["prediction_canonical"]
        if prediction not in label_set:
            prediction = "Ngoài 30 lớp"
        matrix[truth, prediction] += 1
        support[truth] += 1
    cell_w, cell_h, left, top = 48, 32, 500, 300
    image = Image.new("RGB", (left + len(grouped) * cell_w + 140, top + len(labels) * cell_h + 110), "white")
    draw = ImageDraw.Draw(image)
    draw.text((60, 45), "Ma trận nhầm lẫn chuẩn hóa (30 lớp đánh giá)", fill=DARK, font=get_font(46, True))
    draw.text((60, 115), "Hàng: nhãn thật | Cột: nhãn dự đoán", fill=MUTED, font=get_font(28))
    label_font = get_font(17)
    for column, label in enumerate(grouped):
        x = left + column * cell_w + cell_w // 2
        column_label = display_names.get(label, label)
        bbox = label_font.getbbox(column_label)
        label_image = Image.new("RGBA", (bbox[2] - bbox[0] + 8, bbox[3] - bbox[1] + 8), (255, 255, 255, 0))
        label_draw = ImageDraw.Draw(label_image)
        label_draw.text((4 - bbox[0], 4 - bbox[1]), column_label, fill=DARK, font=label_font)
        label_image = label_image.rotate(90, expand=True)
        image.paste(label_image, (x - label_image.width // 2, top - label_image.height - 12), label_image)
    for row_index, truth in enumerate(labels):
        y = top + row_index * cell_h
        draw.text((left - 20, y + cell_h // 2), display_names.get(truth, truth), anchor="rm", fill=DARK, font=get_font(16))
        for column, prediction in enumerate(grouped):
            value = matrix[truth, prediction] / support[truth] if support[truth] else 0.0
            intensity = int(245 - 190 * value)
            color = (intensity, 245, intensity) if truth == prediction else (255, intensity, intensity)
            x = left + column * cell_w
            draw.rectangle((x, y, x + cell_w - 1, y + cell_h - 1), fill=color)
            if value >= 0.03:
                draw.text((x + cell_w // 2, y + cell_h // 2), f"{value * 100:.0f}",
                          anchor="mm", fill=DARK, font=get_font(10, True))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, quality=95)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate all images in the clean 30VNFoods test manifest.")
    parser.add_argument("--project", type=Path, default=Path("D:/appfood4"))
    parser.add_argument("--report", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--batch-size", type=int, default=4)
    args = parser.parse_args()
    args.project = args.project.resolve()
    args.report = args.report.resolve()
    args.model = args.project / "backend/models/vietnamese_food_classifier"
    args.manifest = args.project / "datasets/processed/30VNFoods_clean/manifests/test.csv"
    args.output = args.report / "evaluation/predictions.csv"
    sys.path.insert(0, str(args.project))
    from backend.recipes.normalizer import normalize_dish_name

    run_predictions(args, normalize_dish_name)
    metrics = calculate_metrics(args.output, args.report / "evaluation", args.project)
    if metrics["sample_count"] != len(read_manifest(args.manifest)):
        raise RuntimeError("Evaluation is incomplete; metrics are not accepted.")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
