from __future__ import annotations

import unittest
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import jwt
from fastapi import HTTPException
from starlette.requests import Request
from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import sessionmaker

from backend.config import AUTH_SECRET_KEY, _resolve_auth_secret
from backend.db import Base, create_database_engine
from backend.models import PredictionFeedback, PredictionHistory, User
from backend.rate_limit import InMemoryRateLimiter
from backend.scripts.import_recipes import read_records
from backend.security import ALGORITHM, decode_token


class SecurityTests(unittest.TestCase):
    def test_development_secret_is_ephemeral_and_production_requires_a_strong_secret(self):
        first = _resolve_auth_secret("development", None)
        second = _resolve_auth_secret("development", None)
        self.assertNotEqual(first, second)
        self.assertGreaterEqual(len(first.encode("utf-8")), 32)

        with self.assertRaises(RuntimeError):
            _resolve_auth_secret("production", None)
        with self.assertRaises(RuntimeError):
            _resolve_auth_secret("production", "too-short")

        strong = "a" * 32
        self.assertEqual(_resolve_auth_secret("production", strong), strong)

    def test_tokens_with_missing_or_invalid_required_claims_return_401(self):
        now = datetime.now(timezone.utc)
        base = {
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "type": "access",
            "jti": "test-jti",
        }
        invalid_payloads = (
            base,
            {**base, "sub": "not-an-integer"},
            {key: value for key, value in {**base, "sub": "1"}.items() if key != "jti"},
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                token = jwt.encode(payload, AUTH_SECRET_KEY, algorithm=ALGORITHM)
                with self.assertRaises(HTTPException) as raised:
                    decode_token(token, "access")
                self.assertEqual(raised.exception.status_code, 401)

    def test_rate_limiter_returns_429_after_the_configured_limit(self):
        limiter = InMemoryRateLimiter()
        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/predict",
                "headers": [],
                "query_string": b"",
                "scheme": "http",
                "server": ("testserver", 80),
                "client": ("127.0.0.1", 12345),
            }
        )
        limiter.check(request, bucket="test", limit=2)
        limiter.check(request, bucket="test", limit=2)
        with self.assertRaises(HTTPException) as raised:
            limiter.check(request, bucket="test", limit=2)
        self.assertEqual(raised.exception.status_code, 429)
        self.assertIn("Retry-After", raised.exception.headers)


class SqliteTests(unittest.TestCase):
    def test_foreign_keys_are_enabled_and_history_delete_cascades_feedback(self):
        engine = create_database_engine("sqlite://")
        Session = sessionmaker(bind=engine, expire_on_commit=False)
        try:
            Base.metadata.create_all(bind=engine)
            with engine.connect() as connection:
                self.assertEqual(connection.execute(text("PRAGMA foreign_keys")).scalar(), 1)

            with Session() as db:
                user = User(
                    email="cascade@example.com",
                    full_name="Cascade Test",
                    password_hash="not-used-in-this-test",
                )
                db.add(user)
                db.flush()
                history = PredictionHistory(
                    id="00000000-0000-0000-0000-000000000001",
                    user_id=user.id,
                    predicted_dish="Phở",
                    confidence=0.9,
                    top3_json="[]",
                )
                db.add(history)
                db.flush()
                db.add(
                    PredictionFeedback(
                        history_id=history.id,
                        user_id=user.id,
                        selected_dish="Phở",
                    )
                )
                db.commit()

                db.execute(delete(PredictionHistory).where(PredictionHistory.id == history.id))
                db.commit()
                feedback_count = db.scalar(
                    select(func.count()).select_from(PredictionFeedback)
                )
                self.assertEqual(feedback_count, 0)
        finally:
            engine.dispose()


class RecipeCsvTests(unittest.TestCase):
    def test_csv_nested_fields_are_parsed_as_json_arrays(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "recipes.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "name",
                        "sourceUrl",
                        "sourceName",
                        "prepMinutes",
                        "cookMinutes",
                        "servings",
                        "aliases",
                        "ingredients",
                        "steps",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "name": "Món thử",
                        "sourceUrl": "https://example.com/recipe",
                        "sourceName": "Nguồn",
                        "prepMinutes": "10",
                        "cookMinutes": "20",
                        "servings": "2",
                        "aliases": '["Tên khác"]',
                        "ingredients": '[{"name":"Gạo","quantity":"200","unit":"g"}]',
                        "steps": '["Vo gạo","Nấu chín"]',
                    }
                )

            records = read_records(path)
            self.assertEqual(records[0]["prepMinutes"], 10)
            self.assertEqual(records[0]["aliases"], ["Tên khác"])
            self.assertEqual(records[0]["ingredients"][0]["name"], "Gạo")
            self.assertEqual(records[0]["steps"], ["Vo gạo", "Nấu chín"])

    def test_csv_rejects_invalid_nested_json_with_a_clear_line_number(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "recipes.csv"
            path.write_text(
                "name,sourceUrl,sourceName,ingredients\n"
                'Món thử,https://example.com/recipe,Nguồn,"not-json"\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "Dòng 2.*ingredients"):
                read_records(path)


if __name__ == "__main__":
    unittest.main()
