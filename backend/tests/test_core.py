from __future__ import annotations

import unittest
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

import torch
from PIL import Image

from backend.ai.model_loader import ModelBundle
from backend.ai.predictor import InvalidImageError, decode_image, predict_image
from backend.recipes.normalizer import normalize_dish_name


def valid_png() -> bytes:
    stream = BytesIO()
    Image.new("RGB", (8, 8), "red").save(stream, format="PNG")
    return stream.getvalue()


class FakeProcessor:
    def __call__(self, **_):
        return {"pixel_values": torch.zeros((1, 3, 2, 2))}


class FakeModel:
    config = SimpleNamespace(id2label={0: "Pho", 1: "Bun rieu", 2: "Com tam"})

    def __call__(self, **_):
        return SimpleNamespace(logits=torch.tensor([[4.0, 1.0, 0.0]]))


class CoreTests(unittest.TestCase):
    def test_rejects_invalid_image(self):
        with self.assertRaises(InvalidImageError):
            decode_image(b"not an image")

    def test_rejects_image_with_excessive_pixel_dimensions(self):
        with patch("backend.ai.predictor.MAX_IMAGE_PIXELS", 10):
            with self.assertRaisesRegex(InvalidImageError, "pixel"):
                decode_image(valid_png())

    def test_prediction_uses_model_labels_and_threshold(self):
        bundle = ModelBundle(FakeProcessor(), FakeModel(), torch.device("cpu"), "fake")
        result = predict_image(valid_png(), bundle=bundle)
        self.assertEqual(result["prediction"]["dish"], "Pho")
        self.assertTrue(result["prediction"]["accepted"])
        self.assertEqual(len(result["top3"]), 3)

    def test_normalizer_has_no_invented_alias(self):
        self.assertEqual(normalize_dish_name("  PHO_bo  "), "pho bo")


if __name__ == "__main__":
    unittest.main()
