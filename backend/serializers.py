from __future__ import annotations

import json
from datetime import datetime, timezone

from backend.models import Dish, PredictionHistory, User


def utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def user_json(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "fullName": user.full_name,
        "createdAt": utc_iso(user.created_at),
    }


def dish_json(dish: Dish, favorite: bool = False, include_recipe: bool = False) -> dict:
    reference_count = len(dish.references)
    origin_ready = (
        dish.content_origin == "translated_open_source" and reference_count >= 1
    ) or (
        dish.content_origin == "original_synthesis" and reference_count >= 2
    )
    has_recipe = bool(
        dish.published
        and dish.source_url
        and dish.source_name
        and dish.source_revision_url
        and dish.source_license_name
        and dish.source_license_url
        and dish.source_attribution
        and dish.content_origin
        and dish.verification_status
        and dish.verification_note
        and origin_ready
        and dish.ingredients
        and dish.steps
        and dish.image_url
        and dish.image_author
        and dish.image_source_url
        and dish.image_license_name
        and dish.image_license_url
    )
    result = {
        "id": dish.id,
        "slug": dish.slug,
        "name": dish.name,
        "aliases": json.loads(dish.aliases_json or "[]"),
        "region": dish.region,
        "category": dish.category,
        "prepMinutes": dish.prep_minutes,
        "cookMinutes": dish.cook_minutes,
        "totalMinutes": dish.total_minutes,
        "difficulty": dish.difficulty,
        "servings": dish.servings,
        "servingsText": dish.servings_text,
        "description": dish.description if has_recipe else None,
        "imageUrl": dish.image_url if has_recipe else None,
        "imageAttribution": dish.image_attribution if has_recipe else None,
        "imageAuthor": dish.image_author if has_recipe else None,
        "imageSourceUrl": dish.image_source_url if has_recipe else None,
        "imageLicenseName": dish.image_license_name if has_recipe else None,
        "imageLicenseUrl": dish.image_license_url if has_recipe else None,
        "hasRecipe": has_recipe,
        "isFavorite": favorite,
    }
    if include_recipe:
        result["recipe"] = (
            {
                "ingredients": [
                    {"name": item.name, "quantity": item.quantity, "unit": item.unit}
                    for item in dish.ingredients
                ],
                "steps": [item.instruction for item in dish.steps],
                "sourceUrl": dish.source_url,
                "sourceName": dish.source_name,
                "sourceRevisionUrl": dish.source_revision_url,
                "licenseName": dish.source_license_name,
                "licenseUrl": dish.source_license_url,
                "attribution": dish.source_attribution,
                "modifiedFromSource": dish.source_modified,
                "contentOrigin": dish.content_origin,
                "verificationStatus": dish.verification_status,
                "verificationNote": dish.verification_note,
                "references": [
                    {
                        "name": item.name,
                        "url": item.url,
                        "publisher": item.publisher,
                        "accessedAt": item.accessed_at,
                    }
                    for item in dish.references
                ],
            }
            if has_recipe
            else None
        )
        result["recipeMessage"] = (
            None if has_recipe else "Chưa có công thức đã kiểm chứng cho món này."
        )
    return result


def history_json(item: PredictionHistory) -> dict:
    return {
        "id": item.id,
        "predictedDish": item.predicted_dish,
        "confidence": item.confidence,
        "top3": json.loads(item.top3_json),
        "selectedDish": item.selected_dish,
        "imageStored": item.image_stored,
        "createdAt": utc_iso(item.created_at),
    }
