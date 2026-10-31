from __future__ import annotations

import json
import os
import unittest
from io import BytesIO
from unittest.mock import patch

from PIL import Image
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


os.environ["MODEL_LOAD_ON_STARTUP"] = "false"

from fastapi.testclient import TestClient

from backend.app import app
from backend.catalog import seed_catalog
from backend.db import Base, get_db
from backend.models import (
    Dish,
    Favorite,
    PredictionFeedback,
    PredictionHistory,
    User,
)
from backend.scripts.import_recipes import import_records, validate, validation_report


def valid_png() -> bytes:
    stream = BytesIO()
    Image.new("RGB", (8, 8), "green").save(stream, format="PNG")
    return stream.getvalue()


class MvpApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.Session = sessionmaker(
            bind=cls.engine,
            autoflush=False,
            expire_on_commit=False,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()

    def setUp(self) -> None:
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        with self.Session() as db:
            seed_catalog(db)

        def override_db():
            db = self.Session()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_db
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        app.dependency_overrides.pop(get_db, None)

    def register(
        self,
        email: str = "owner@example.com",
        password: str = "correct-horse-123",
        full_name: str = "Nguyen An",
    ) -> dict:
        response = self.client.post(
            "/auth/register",
            json={"email": email, "password": password, "fullName": full_name},
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    @staticmethod
    def auth_headers(payload: dict) -> dict[str, str]:
        return {"Authorization": f"Bearer {payload['accessToken']}"}

    def test_auth_register_login_refresh_logout_and_profile(self):
        registered = self.register(email=" Owner@Example.com ")
        self.assertEqual(registered["user"]["email"], "owner@example.com")
        self.assertNotIn("password", registered["user"])

        with self.Session() as db:
            user = db.scalar(select(User).where(User.email == "owner@example.com"))
            self.assertIsNotNone(user)
            self.assertNotEqual(user.password_hash, "correct-horse-123")

        duplicate = self.client.post(
            "/auth/register",
            json={
                "email": "OWNER@example.com",
                "password": "another-password",
                "fullName": "Duplicate User",
            },
        )
        self.assertEqual(duplicate.status_code, 409)

        unauthenticated = self.client.get("/users/me")
        self.assertEqual(unauthenticated.status_code, 401)

        headers = self.auth_headers(registered)
        me = self.client.get("/users/me", headers=headers)
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["fullName"], "Nguyen An")

        updated = self.client.patch(
            "/users/me", json={"fullName": "Nguyen An Updated"}, headers=headers
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["fullName"], "Nguyen An Updated")

        bad_login = self.client.post(
            "/auth/login",
            json={"email": "owner@example.com", "password": "wrong-password"},
        )
        self.assertEqual(bad_login.status_code, 401)

        login = self.client.post(
            "/auth/login",
            json={"email": " OWNER@EXAMPLE.COM ", "password": "correct-horse-123"},
        )
        self.assertEqual(login.status_code, 200, login.text)
        login_payload = login.json()
        self.assertEqual(login_payload["user"]["fullName"], "Nguyen An Updated")

        old_refresh = login_payload["refreshToken"]
        refreshed = self.client.post(
            "/auth/refresh", json={"refreshToken": old_refresh}
        )
        self.assertEqual(refreshed.status_code, 200, refreshed.text)
        refreshed_payload = refreshed.json()
        self.assertNotEqual(refreshed_payload["refreshToken"], old_refresh)
        self.assertEqual(
            self.client.post(
                "/auth/refresh", json={"refreshToken": old_refresh}
            ).status_code,
            401,
        )

        current_refresh = refreshed_payload["refreshToken"]
        logged_out = self.client.post(
            "/auth/logout", json={"refreshToken": current_refresh}
        )
        self.assertEqual(logged_out.status_code, 204)
        self.assertEqual(
            self.client.post(
                "/auth/refresh", json={"refreshToken": current_refresh}
            ).status_code,
            401,
        )

    def test_auth_rejects_invalid_registration_data(self):
        invalid_email = self.client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "password": "long-enough-password",
                "fullName": "Nguyen An",
            },
        )
        self.assertEqual(invalid_email.status_code, 422)

        short_password = self.client.post(
            "/auth/register",
            json={
                "email": "valid@example.com",
                "password": "short",
                "fullName": "Nguyen An",
            },
        )
        self.assertEqual(short_password.status_code, 422)

    def test_dishes_support_unaccented_search_filters_and_pagination(self):
        with self.Session() as db:
            dish = db.scalar(select(Dish).where(Dish.slug == "bun-bo-hue"))
            dish.region = "Miền Trung"
            dish.category = "Món nước"
            dish.prep_minutes = 20
            dish.cook_minutes = 70
            dish.difficulty = "Vừa"
            db.commit()

        unaccented = self.client.get("/dishes", params={"q": "bun bo hue"})
        self.assertEqual(unaccented.status_code, 200)
        self.assertEqual(
            [item["slug"] for item in unaccented.json()["items"]],
            ["bun-bo-hue"],
        )

        filtered = self.client.get(
            "/dishes",
            params={
                "region": "Miền Trung",
                "category": "Món nước",
                "difficulty": "Vừa",
                "maxMinutes": 90,
            },
        )
        self.assertEqual(filtered.status_code, 200)
        self.assertEqual(filtered.json()["total"], 1)
        self.assertEqual(filtered.json()["items"][0]["slug"], "bun-bo-hue")

        too_short = self.client.get(
            "/dishes", params={"region": "Miền Trung", "maxMinutes": 89}
        )
        self.assertEqual(too_short.status_code, 200)
        self.assertEqual(too_short.json()["total"], 0)

        page_one = self.client.get("/dishes", params={"page": 1, "limit": 5})
        page_two = self.client.get("/dishes", params={"page": 2, "limit": 5})
        self.assertEqual(page_one.status_code, 200)
        self.assertEqual(page_two.status_code, 200)
        self.assertEqual(page_one.json()["page"], 1)
        self.assertEqual(page_two.json()["page"], 2)
        self.assertEqual(page_one.json()["limit"], 5)
        self.assertEqual(page_one.json()["total"], page_two.json()["total"])
        self.assertEqual(len(page_one.json()["items"]), 5)
        self.assertEqual(len(page_two.json()["items"]), 5)
        self.assertTrue(
            {item["slug"] for item in page_one.json()["items"]}.isdisjoint(
                {item["slug"] for item in page_two.json()["items"]}
            )
        )

    def test_favorites_are_private_to_the_authenticated_owner(self):
        owner = self.register()
        stranger = self.register(
            email="stranger@example.com", full_name="Tran Binh"
        )
        owner_headers = self.auth_headers(owner)
        stranger_headers = self.auth_headers(stranger)

        self.assertEqual(self.client.get("/favorites").status_code, 401)
        added = self.client.post(
            "/favorites", json={"dishSlug": "pho"}, headers=owner_headers
        )
        self.assertEqual(added.status_code, 201, added.text)
        self.assertTrue(added.json()["isFavorite"])

        # Adding the same dish is idempotent and must not create duplicates.
        duplicate = self.client.post(
            "/favorites", json={"dishSlug": "pho"}, headers=owner_headers
        )
        self.assertEqual(duplicate.status_code, 201)
        with self.Session() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(Favorite)), 1)

        self.assertEqual(
            self.client.get("/favorites", headers=stranger_headers).json()["items"],
            [],
        )
        stranger_delete = self.client.delete(
            "/favorites/pho", headers=stranger_headers
        )
        self.assertEqual(stranger_delete.status_code, 204)
        owner_items = self.client.get("/favorites", headers=owner_headers).json()[
            "items"
        ]
        self.assertEqual([item["slug"] for item in owner_items], ["pho"])

        owner_delete = self.client.delete("/favorites/pho", headers=owner_headers)
        self.assertEqual(owner_delete.status_code, 204)
        self.assertEqual(
            self.client.get("/favorites", headers=owner_headers).json()["items"],
            [],
        )

    @patch("backend.app.predict_image")
    def test_authenticated_prediction_saves_history_without_image(self, mocked_predict):
        mocked_predict.return_value = {
            "prediction": {"dish": "Phở", "confidence": 0.91, "accepted": True},
            "top3": [
                {"dish": "Phở", "confidence": 0.91},
                {"dish": "Bún bò Huế", "confidence": 0.06},
                {"dish": "Hủ tiếu", "confidence": 0.03},
            ],
        }
        owner = self.register()
        headers = self.auth_headers(owner)

        response = self.client.post(
            "/predict",
            files={"image": ("private-food.png", valid_png(), "image/png")},
            headers=headers,
        )
        self.assertEqual(response.status_code, 200, response.text)
        prediction_id = response.json()["predictionId"]
        self.assertIsNotNone(prediction_id)

        history = self.client.get("/history", headers=headers)
        self.assertEqual(history.status_code, 200)
        self.assertEqual(len(history.json()["items"]), 1)
        saved = history.json()["items"][0]
        self.assertEqual(saved["id"], prediction_id)
        self.assertFalse(saved["imageStored"])
        self.assertNotIn("image", saved)
        self.assertNotIn("imageUrl", saved)
        self.assertEqual(len(saved["top3"]), 3)

        with self.Session() as db:
            row = db.get(PredictionHistory, prediction_id)
            self.assertIsNotNone(row)
            self.assertFalse(row.image_stored)
            self.assertNotIn("image", PredictionHistory.__table__.columns.keys())
            self.assertNotIn("image_bytes", PredictionHistory.__table__.columns.keys())
            self.assertEqual(json.loads(row.top3_json), mocked_predict.return_value["top3"])

        anonymous = self.client.post(
            "/predict",
            files={"image": ("anonymous-food.png", valid_png(), "image/png")},
        )
        self.assertEqual(anonymous.status_code, 200)
        self.assertIsNone(anonymous.json()["predictionId"])
        self.assertEqual(
            len(self.client.get("/history", headers=headers).json()["items"]), 1
        )

    @patch("backend.app.predict_image")
    def test_feedback_and_history_enforce_ownership(self, mocked_predict):
        mocked_predict.return_value = {
            "prediction": {"dish": "Phở", "confidence": 0.7, "accepted": True},
            "top3": [{"dish": "Phở", "confidence": 0.7}],
        }
        owner = self.register()
        stranger = self.register(
            email="stranger@example.com", full_name="Tran Binh"
        )
        owner_headers = self.auth_headers(owner)
        stranger_headers = self.auth_headers(stranger)
        predicted = self.client.post(
            "/predict",
            files={"image": ("food.png", valid_png(), "image/png")},
            headers=owner_headers,
        )
        prediction_id = predicted.json()["predictionId"]

        forbidden_feedback = self.client.post(
            f"/predictions/{prediction_id}/feedback",
            json={"selectedDish": "Bún bò Huế"},
            headers=stranger_headers,
        )
        self.assertEqual(forbidden_feedback.status_code, 404)
        forbidden_delete = self.client.delete(
            f"/history/{prediction_id}", headers=stranger_headers
        )
        self.assertEqual(forbidden_delete.status_code, 404)

        feedback = self.client.post(
            f"/predictions/{prediction_id}/feedback",
            json={"selectedDish": "Bún bò Huế"},
            headers=owner_headers,
        )
        self.assertEqual(feedback.status_code, 200, feedback.text)
        self.assertEqual(feedback.json()["selectedDish"], "Bún bò Huế")

        updated = self.client.post(
            f"/predictions/{prediction_id}/feedback",
            json={"selectedDish": "Hủ tiếu"},
            headers=owner_headers,
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["selectedDish"], "Hủ tiếu")
        with self.Session() as db:
            feedback_rows = db.scalars(
                select(PredictionFeedback).where(
                    PredictionFeedback.history_id == prediction_id
                )
            ).all()
            self.assertEqual(len(feedback_rows), 1)
            self.assertEqual(feedback_rows[0].selected_dish, "Hủ tiếu")
            self.assertEqual(feedback_rows[0].user_id, owner["user"]["id"])

        owner_history = self.client.get("/history", headers=owner_headers).json()[
            "items"
        ]
        stranger_history = self.client.get(
            "/history", headers=stranger_headers
        ).json()["items"]
        self.assertEqual(owner_history[0]["selectedDish"], "Hủ tiếu")
        self.assertEqual(stranger_history, [])

    def test_recipe_import_requires_a_verifiable_source(self):
        invalid_records = (
            ({"sourceUrl": "https://example.com/recipe", "sourceName": "Nguồn"}, "name"),
            ({"name": "Món thử", "sourceName": "Nguồn"}, "sourceUrl"),
            ({"name": "Món thử", "sourceUrl": "https://example.com/recipe"}, "sourceName"),
        )
        for record, missing_field in invalid_records:
            with self.subTest(missing=missing_field):
                with self.assertRaisesRegex(ValueError, missing_field):
                    validate(record)

        with self.assertRaisesRegex(ValueError, "HTTP"):
            validate(
                {
                    "name": "Món thử",
                    "sourceUrl": "ftp://example.com/recipe",
                    "sourceName": "Nguồn kiểm chứng",
                    "sourceRevisionUrl": "https://example.com/recipe?oldid=1",
                    "sourceLicenseName": "CC BY-SA 4.0",
                    "sourceLicenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/",
                    "sourceAttribution": "Tác giả thử nghiệm",
                    "sourceModified": True,
                }
            )

        sourced_recipe = {
            "name": "Món thử có nguồn",
            "region": "Miền Nam",
            "category": "Món chính",
            "sourceUrl": "https://example.com/verified-recipe",
            "sourceName": "Nguồn kiểm chứng",
            "sourceRevisionUrl": "https://example.com/verified-recipe?oldid=1",
            "sourceLicenseName": "CC BY-SA 4.0",
            "sourceLicenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/",
            "sourceAttribution": "Tác giả thử nghiệm",
            "sourceModified": True,
            "contentOrigin": "translated_open_source",
            "verificationStatus": "source_verified",
            "verificationNote": "Đã đối chiếu phiên bản cố định.",
            "prepMinutes": 10,
            "cookMinutes": 0,
            "totalMinutes": 10,
            "servings": 2,
            "servingsText": "2 phần",
            "metadataSourceUrl": "https://example.com/verified-recipe?oldid=1",
            "references": [
                {
                    "name": "Nguồn kiểm chứng",
                    "url": "https://example.com/verified-recipe?oldid=1",
                    "publisher": "Nhà xuất bản thử nghiệm",
                    "accessedAt": "2026-10-10",
                }
            ],
            "imageUrl": "/media/dishes/mon-thu-co-nguon.webp",
            "imageAttribution": "Tác giả ảnh · CC BY 4.0",
            "imageAuthor": "Tác giả ảnh",
            "imageSourceUrl": "https://example.com/image",
            "imageLicenseName": "CC BY 4.0",
            "imageLicenseUrl": "https://creativecommons.org/licenses/by/4.0/",
            "ingredients": [
                {"name": "Nguyên liệu thật", "quantity": "1", "unit": "phần"}
            ],
            "steps": ["Thực hiện theo nguồn đã dẫn."],
        }
        validate(sourced_recipe)
        with (
            patch("backend.scripts.import_recipes.SessionLocal", self.Session),
            patch("backend.scripts.import_recipes.migrate_database"),
            patch("backend.scripts.import_recipes.seed_catalog"),
        ):
            self.assertEqual(import_records([sourced_recipe]), 1)
            with self.Session() as db:
                dish_id = db.scalar(
                    select(Dish.id).where(Dish.slug == "mon-thu-co-nguon")
                )
                imported_dish = db.scalar(
                    select(Dish).where(Dish.slug == "mon-thu-co-nguon")
                )
                self.assertEqual(imported_dish.cook_minutes, 0)
                self.assertEqual(imported_dish.servings_text, "2 phần")
            self.assertEqual(import_records([sourced_recipe]), 1)
            with self.Session() as db:
                self.assertEqual(
                    db.scalar(
                        select(func.count()).select_from(Dish).where(
                            Dish.slug == "mon-thu-co-nguon"
                        )
                    ),
                    1,
                )
                self.assertEqual(
                    db.scalar(select(Dish.id).where(Dish.slug == "mon-thu-co-nguon")),
                    dish_id,
                )

        detail = self.client.get("/dishes/mon-thu-co-nguon")
        self.assertEqual(detail.status_code, 200, detail.text)
        payload = detail.json()
        self.assertTrue(payload["hasRecipe"])
        self.assertEqual(
            payload["recipe"]["sourceUrl"],
            "https://example.com/verified-recipe",
        )
        self.assertEqual(payload["recipe"]["sourceName"], "Nguồn kiểm chứng")
        self.assertEqual(payload["recipe"]["licenseName"], "CC BY-SA 4.0")
        self.assertEqual(
            payload["recipe"]["ingredients"][0]["name"], "Nguyên liệu thật"
        )
        self.assertEqual(payload["prepMinutes"], 10)
        self.assertEqual(payload["cookMinutes"], 0)
        self.assertEqual(payload["totalMinutes"], 10)
        self.assertEqual(payload["servingsText"], "2 phần")

        for field, value in (
            ("prepMinutes", None),
            ("cookMinutes", -1),
            ("totalMinutes", 0),
            ("servingsText", ""),
        ):
            invalid = dict(sourced_recipe)
            invalid[field] = value
            with self.subTest(invalid_field=field):
                with self.assertRaises(ValueError):
                    validate(invalid)

        missing_metadata_reference = dict(sourced_recipe)
        missing_metadata_reference["metadataSourceUrl"] = (
            "https://example.com/not-in-references"
        )
        with self.assertRaisesRegex(ValueError, "references"):
            validate(missing_metadata_reference)

    def test_recipe_validation_report_lists_every_invalid_record(self):
        report = validation_report(
            [
                {"slug": "thieu-nguon", "name": "Thiếu nguồn"},
                {"slug": "thieu-nguon-2", "name": "Thiếu nguồn 2"},
            ]
        )
        self.assertEqual(report["valid"], 0)
        self.assertEqual(report["invalid"], 2)
        self.assertEqual(
            [item["slug"] for item in report["errors"]],
            ["thieu-nguon", "thieu-nguon-2"],
        )

    def test_recipe_import_is_atomic_when_one_record_is_invalid(self):
        valid = {
            "name": "Món hợp lệ",
            "sourceUrl": "https://example.com/recipe",
            "sourceName": "Nguồn",
            "sourceRevisionUrl": "https://example.com/recipe?oldid=1",
            "sourceLicenseName": "CC BY-SA 4.0",
            "sourceLicenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/",
            "sourceAttribution": "Tác giả thử nghiệm",
            "sourceModified": True,
            "ingredients": [{"name": "Nguyên liệu"}],
            "steps": ["Một bước có nguồn."],
        }
        with self.Session() as db:
            before = db.scalar(select(func.count()).select_from(Dish))
        with self.assertRaises(ValueError):
            import_records([valid, {"name": "Món lỗi"}])
        with self.Session() as db:
            after = db.scalar(select(func.count()).select_from(Dish))
            self.assertIsNone(
                db.scalar(select(Dish).where(Dish.slug == "mon-hop-le"))
            )
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
