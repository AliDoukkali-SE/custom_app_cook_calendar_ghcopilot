from datetime import date
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Ingredient(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    quantity: float | None = None
    unit: str | None = None  # g, kg, L, pièce, etc.
    category: Literal["légumes", "protéines", "féculents", "autres"] = "autres"


class Meal(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    date: date
    slot: Literal["breakfast", "lunch", "dinner"]
    name: str = Field(..., min_length=1, max_length=120)
    notes: str | None = None
    calories: int | None = None
    ingredients: list[Ingredient] = Field(default_factory=list)


class MealCreate(BaseModel):
    date: date
    slot: Literal["breakfast", "lunch", "dinner"]
    name: str = Field(..., min_length=1, max_length=120)
    notes: str | None = None
    calories: int | None = None
    ingredients: list[Ingredient] = Field(default_factory=list)


class MealUpdate(BaseModel):
    date: date
    slot: Literal["breakfast", "lunch", "dinner"]
    name: str = Field(..., min_length=1, max_length=120)
    notes: str | None = None
    calories: int | None = None
    ingredients: list[Ingredient] = Field(default_factory=list)
