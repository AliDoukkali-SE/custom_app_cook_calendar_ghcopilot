from __future__ import annotations

# Backward-compatibility layer for legacy imports (app.models).
from .schemas import DuplicateWeekRequest, Meal, MealCreate, MealUpdate, WeekFilter

__all__ = [
    "Meal",
    "MealCreate",
    "MealUpdate",
    "WeekFilter",
    "DuplicateWeekRequest",
]
