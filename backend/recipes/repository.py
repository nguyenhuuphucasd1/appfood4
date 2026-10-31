from __future__ import annotations

from typing import Any, Protocol


class RecipeRepository(Protocol):
    def find_by_canonical_name(self, canonical_name: str) -> dict[str, Any] | None: ...


class EmptyRecipeRepository:
    """Safe placeholder until a traceable recipe data source is supplied."""

    def find_by_canonical_name(self, canonical_name: str) -> None:
        return None


recipe_repository: RecipeRepository = EmptyRecipeRepository()

