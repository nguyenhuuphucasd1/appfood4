from __future__ import annotations

from io import BytesIO
from threading import Lock
from typing import Any

import torch
from PIL import Image, UnidentifiedImageError

from backend.ai.model_loader import ModelBundle, get_model_bundle
from backend.config import CONFIDENCE_THRESHOLD, MAX_IMAGE_PIXELS, TOP_K


class InvalidImageError(ValueError):
    """Raised when uploaded bytes are not a supported, readable image."""


_INFERENCE_LOCK = Lock()


def decode_image(image_bytes: bytes) -> Image.Image:
    if not image_bytes:
        raise InvalidImageError("Tệp ảnh rỗng.")
    try:
        with Image.open(BytesIO(image_bytes)) as source:
            if source.format not in {"JPEG", "PNG"}:
                raise InvalidImageError("Chỉ hỗ trợ ảnh JPEG, JPG hoặc PNG.")
            if source.width * source.height > MAX_IMAGE_PIXELS:
                raise InvalidImageError("Ảnh có kích thước pixel quá lớn.")
            source.verify()
        with Image.open(BytesIO(image_bytes)) as source:
            return source.convert("RGB")
    except InvalidImageError:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise InvalidImageError("Ảnh bị lỗi hoặc không đọc được.") from exc


def _label_for(model: Any, index: int) -> str:
    labels = model.config.id2label
    return str(labels.get(index, labels.get(str(index), f"LABEL_{index}")))


def predict_image(
    image_bytes: bytes,
    *,
    bundle: ModelBundle | None = None,
    top_k: int = TOP_K,
    threshold: float = CONFIDENCE_THRESHOLD,
) -> dict[str, Any]:
    image = decode_image(image_bytes)
    active_bundle = bundle or get_model_bundle()

    # The model is a singleton and large enough that parallel CPU inference can
    # exhaust memory. Serialize only the processor/model section while FastAPI's
    # event loop remains free because predict_image runs in a worker thread.
    with _INFERENCE_LOCK:
        inputs = active_bundle.processor(images=image, return_tensors="pt")
        inputs = {name: tensor.to(active_bundle.device) for name, tensor in inputs.items()}

        with torch.inference_mode():
            logits = active_bundle.model(**inputs).logits
            probabilities = torch.softmax(logits, dim=-1)[0]

    count = min(top_k, int(probabilities.shape[-1]))
    scores, indices = torch.topk(probabilities, k=count)
    top_predictions = [
        {
            "dish": _label_for(active_bundle.model, int(index.item())),
            "confidence": round(float(score.item()), 6),
        }
        for score, index in zip(scores, indices, strict=True)
    ]
    best = top_predictions[0]
    return {
        "prediction": {
            **best,
            "accepted": best["confidence"] >= threshold,
        },
        "top3": top_predictions,
    }
