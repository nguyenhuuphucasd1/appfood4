from __future__ import annotations

import logging
import json
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from starlette.concurrency import run_in_threadpool

from backend.ai.model_loader import ModelLoadError, get_model_bundle
from backend.ai.predictor import InvalidImageError, predict_image
from backend.config import (
    CORS_ORIGINS,
    MAX_IMAGE_BYTES,
    MODEL_LOAD_ON_STARTUP,
    STATIC_DIR,
    SUPPORTED_CONTENT_TYPES,
)
from backend.catalog import normalize_text, seed_catalog
from backend.db import SessionLocal, get_db
from backend.migrations.runner import migrate_database
from backend.models import Dish, PredictionHistory, User
from backend.rate_limit import predict_rate_limit
from backend.recipes.normalizer import normalize_dish_name
from backend.routers import activity, auth, dishes, users
from backend.security import get_optional_user
from backend.serializers import dish_json


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if MODEL_LOAD_ON_STARTUP:
        get_model_bundle()
    yield


app = FastAPI(
    title="Vietnamese Food Recognition API",
    version="1.1.0",
    description="Nhận diện món ăn bằng pretrained ViT; không tự tạo dữ liệu công thức.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(CORS_ORIGINS),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(STATIC_DIR)), name="media")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(dishes.router)
app.include_router(activity.router)

# Apply versioned migrations before accepting requests. This also keeps simple
# script/test clients working when they do not enter the lifespan context.
migrate_database()
with SessionLocal() as _startup_db:
    seed_catalog(_startup_db)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict")
async def predict(
    image: UploadFile = File(...),
    _: None = Depends(predict_rate_limit),
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> dict:
    # Some mobile pickers do not preserve the MIME type and upload a valid
    # JPEG/PNG as application/octet-stream. Let Pillow perform the authoritative
    # format check below while still rejecting explicitly unsupported media.
    if image.content_type not in SUPPORTED_CONTENT_TYPES | {
        "application/octet-stream",
    }:
        raise HTTPException(status_code=415, detail="Chỉ hỗ trợ ảnh JPEG, JPG hoặc PNG.")

    image_bytes = await image.read(MAX_IMAGE_BYTES + 1)
    await image.close()
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Ảnh vượt quá giới hạn 10 MB.")

    try:
        result = await run_in_threadpool(predict_image, image_bytes)
    except InvalidImageError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ModelLoadError as exc:
        logger.exception("Model is unavailable")
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail="Không thể nhận diện ảnh lúc này.") from exc

    canonical_name = normalize_dish_name(result["prediction"]["dish"])
    dish = db.scalar(
        select(Dish)
        .options(
            selectinload(Dish.ingredients),
            selectinload(Dish.steps),
            selectinload(Dish.references),
        )
        .where(Dish.normalized_name == normalize_text(canonical_name))
    )
    recipe = None
    if dish is not None:
        recipe = dish_json(dish, include_recipe=True).get("recipe")

    prediction_id = None
    if user is not None:
        prediction_id = str(uuid4())
        db.add(
            PredictionHistory(
                id=prediction_id,
                user_id=user.id,
                predicted_dish=result["prediction"]["dish"],
                confidence=float(result["prediction"]["confidence"]),
                top3_json=json.dumps(result["top3"], ensure_ascii=False),
                image_stored=False,
            )
        )
        db.commit()
    return {
        "success": True,
        **result,
        "predictionId": prediction_id,
        "canonicalDish": canonical_name,
        "recognizedDish": dish_json(dish) if dish is not None else None,
        "recipe": recipe,
        "recipeMessage": None if recipe else "Chưa có công thức đã kiểm chứng cho món này.",
    }


@app.exception_handler(ModelLoadError)
async def model_error_handler(_, exc: ModelLoadError) -> JSONResponse:
    return JSONResponse(status_code=503, content={"success": False, "detail": str(exc)})
