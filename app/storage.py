from __future__ import annotations

# Backward-compatibility layer for legacy imports (app.storage).
from .repositories import JsonMealRepository as JsonFileStore
from .repositories import MealRepository as MealStore

__all__ = ["MealStore", "JsonFileStore"]
