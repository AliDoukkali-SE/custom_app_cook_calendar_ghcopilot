from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from uuid import UUID, uuid4
from datetime import date


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
    notes: Optional[str] = None
    calories: int | None = None
    ingredients: List[Ingredient] = []
