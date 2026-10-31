from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from transformers import AutoImageProcessor, AutoModelForImageClassification

from backend.config import MODEL_DIR, MODEL_NAME


REQUIRED_CONFIG_FILES = ("config.json", "preprocessor_config.json")
WEIGHT_PATTERNS = ("*.safetensors", "pytorch_model*.bin")


class ModelLoadError(RuntimeError):
    """Raised when the classifier cannot be made ready for inference."""


@dataclass(frozen=True)
class ModelBundle:
    processor: Any
    model: Any
    device: torch.device
    source: str


_bundle: ModelBundle | None = None
_lock = threading.Lock()


def has_complete_local_model(model_dir: Path = MODEL_DIR) -> bool:
    if not model_dir.is_dir():
        return False
    if any(not (model_dir / name).is_file() for name in REQUIRED_CONFIG_FILES):
        return False
    return any(path.is_file() for pattern in WEIGHT_PATTERNS for path in model_dir.glob(pattern))


def _download_and_save(model_dir: Path) -> tuple[Any, Any]:
    model_dir.mkdir(parents=True, exist_ok=True)
    processor = AutoImageProcessor.from_pretrained(MODEL_NAME)
    model = AutoModelForImageClassification.from_pretrained(MODEL_NAME)
    processor.save_pretrained(model_dir)
    model.save_pretrained(model_dir, safe_serialization=True)

    if not has_complete_local_model(model_dir):
        raise ModelLoadError(f"Model download completed but required files are missing in {model_dir}")
    return processor, model


def load_model_bundle(model_dir: Path = MODEL_DIR) -> ModelBundle:
    try:
        if has_complete_local_model(model_dir):
            processor = AutoImageProcessor.from_pretrained(model_dir, local_files_only=True)
            model = AutoModelForImageClassification.from_pretrained(
                model_dir, local_files_only=True
            )
            source = str(model_dir)
        else:
            processor, model = _download_and_save(model_dir)
            source = MODEL_NAME

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        model.eval()
        return ModelBundle(processor=processor, model=model, device=device, source=source)
    except ModelLoadError:
        raise
    except Exception as exc:
        raise ModelLoadError(
            "Không thể tải model. Hãy kiểm tra kết nối mạng hoặc chạy "
            "`python backend/scripts/download_model.py` trước."
        ) from exc


def get_model_bundle() -> ModelBundle:
    """Return the process-wide model bundle, loading it exactly once."""
    global _bundle
    if _bundle is None:
        with _lock:
            if _bundle is None:
                _bundle = load_model_bundle()
    return _bundle

