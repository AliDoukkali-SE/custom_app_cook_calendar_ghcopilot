from __future__ import annotations

from datetime import date
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Meal(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    date: date
    slot: Literal["breakfast", "lunch", "dinner"]
    name: str = Field(..., min_length=1, max_length=120)
    notes: str | None = None
    calories: int | None = None
    owner_id: UUID


class MealCreate(BaseModel):
    date: date
    slot: Literal["breakfast", "lunch", "dinner"]
    name: str = Field(..., min_length=1, max_length=120)
    notes: str | None = None
    calories: int | None = None


class MealUpdate(BaseModel):
    date: date
    slot: Literal["breakfast", "lunch", "dinner"]
    name: str = Field(..., min_length=1, max_length=120)
    notes: str | None = None
    calories: int | None = None


class WeekFilter(BaseModel):
    year: int = Field(..., ge=1, le=9999)
    week: int = Field(..., ge=1, le=53)


class DuplicateWeekRequest(BaseModel):
    source: WeekFilter
    target: WeekFilter
