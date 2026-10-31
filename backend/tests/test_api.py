from __future__ import annotations

import os
import unittest
from io import BytesIO
from unittest.mock import patch

from PIL import Image


os.environ["MODEL_LOAD_ON_STARTUP"] = "false"

from fastapi.testclient import TestClient

from backend.app import app
from backend.catalog import DISH_NAMES, slugify


def valid_png() -> bytes:
    stream = BytesIO()
    Image.new("RGB", (8, 8), "green").save(stream, format="PNG")
    return stream.getvalue()


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_and_openapi(self):
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})
        self.assertIn("/predict", self.client.get("/openapi.json").json()["paths"])

    def test_published_recipe_catalog_and_local_media(self):
        expected = {slugify(name) for name in DISH_NAMES}
        listing = self.client.get("/dishes", params={"limit": 100})
        self.assertEqual(listing.status_code, 200, listing.text)
        published = {
            item["slug"] for item in listing.json()["items"] if item["hasRecipe"]
        }
        self.assertEqual(published, expected)
        self.assertEqual(len(listing.json()["items"]), 38)
        for item in listing.json()["items"]:
            with self.subTest(slug=item["slug"]):
                self.assertIsNotNone(item["prepMinutes"])
                self.assertIsNotNone(item["cookMinutes"])
                self.assertGreater(item["totalMinutes"], 0)
                self.assertTrue(item["servingsText"].strip())

        pho = self.client.get("/dishes/pho")
        self.assertEqual(pho.status_code, 200, pho.text)
        self.assertEqual(pho.json()["imageUrl"], "/media/dishes/pho.webp")
        self.assertEqual(pho.json()["recipe"]["licenseName"], "CC BY-SA 4.0")
        self.assertTrue(pho.json()["recipe"]["modifiedFromSource"])
        self.assertEqual(
            pho.json()["recipe"]["contentOrigin"], "translated_open_source"
        )

        compiled = self.client.get("/dishes/banh-beo")
        self.assertEqual(compiled.status_code, 200, compiled.text)
        self.assertTrue(compiled.json()["hasRecipe"])
        self.assertEqual(
            compiled.json()["recipe"]["contentOrigin"], "original_synthesis"
        )
        self.assertGreaterEqual(len(compiled.json()["recipe"]["references"]), 2)

        no_cook = self.client.get("/dishes/nem-chua")
        self.assertEqual(no_cook.status_code, 200, no_cook.text)
        self.assertEqual(no_cook.json()["cookMinutes"], 0)
        self.assertEqual(no_cook.json()["totalMinutes"], 4320)
        self.assertEqual(no_cook.json()["servingsText"], "20 cuốn")

        image = self.client.get("/media/dishes/pho.webp")
        self.assertEqual(image.status_code, 200)
        self.assertEqual(image.headers["content-type"], "image/webp")
        self.assertEqual(
            self.client.get("/media/%2e%2e/data/vi_viet.db").status_code,
            404,
        )

    @patch("backend.app.predict_image")
    def test_predict_contract_keeps_top3_and_maps_the_recognized_dish(self, mocked_predict):
        mocked_predict.return_value = {
            "prediction": {"dish": "Bun rieu", "confidence": 0.55, "accepted": False},
            "top3": [
                {"dish": "Bun rieu", "confidence": 0.55},
                {"dish": "Pho", "confidence": 0.25},
                {"dish": "Hu tieu", "confidence": 0.1},
            ],
        }
        response = self.client.post(
            "/predict", files={"image": ("food.png", valid_png(), "image/png")}
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["prediction"]["accepted"])
        self.assertEqual(len(payload["top3"]), 3)
        self.assertEqual(payload["canonicalDish"], "bun rieu")
        self.assertEqual(payload["recognizedDish"]["slug"], "bun-rieu")
        self.assertEqual(payload["recognizedDish"]["name"], "Bún riêu")
        self.assertIsNotNone(payload["recipe"])

    def test_rejects_unsupported_and_corrupt_files(self):
        unsupported = self.client.post(
            "/predict", files={"image": ("file.txt", b"bad", "text/plain")}
        )
        self.assertEqual(unsupported.status_code, 415)

        corrupt = self.client.post(
            "/predict", files={"image": ("food.png", b"bad", "image/png")}
        )
        self.assertEqual(corrupt.status_code, 422)

    @patch("backend.app.predict_image")
    def test_accepts_valid_mobile_octet_stream_upload(self, mocked_predict):
        mocked_predict.return_value = {
            "prediction": {"dish": "Pho", "confidence": 0.9, "accepted": True},
            "top3": [{"dish": "Pho", "confidence": 0.9}],
        }
        response = self.client.post(
            "/predict",
            files={
                "image": (
                    "image_picker.png",
                    valid_png(),
                    "application/octet-stream",
                )
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["prediction"]["dish"], "Pho")
        self.assertTrue(
            response.json()["recipe"]["sourceName"].startswith("Wikibooks")
        )


if __name__ == "__main__":
    unittest.main()
