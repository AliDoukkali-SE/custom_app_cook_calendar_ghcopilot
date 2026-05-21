# Pydantic v2 models with User and multi-tenant Meal
# User: id (UUID), email, display_name
# Meal: includes owner_id (UUID) referencing a User
from pydantic import BaseModel, Field
from typing import Literal, Optional
from uuid import UUID, uuid4
from datetime import date


class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    email: str
    display_name: str


class Meal(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    date: date
    slot: Literal["breakfast", "lunch", "dinner"]
    name: str = Field(..., min_length=1, max_length=120)
    notes: Optional[str] = None
    calories: int | None = None
    owner_id: UUID


class MealCreate(BaseModel):
    """Request model for creating a meal (owner_id set from header)"""
    date: date
    slot: Literal["breakfast", "lunch", "dinner"]
    name: str = Field(..., min_length=1, max_length=120)
    notes: Optional[str] = None
    calories: int | None = None


class MealUpdate(BaseModel):
    """Request model for updating a meal (owner_id set from header)"""
    date: date
    slot: Literal["breakfast", "lunch", "dinner"]
    name: str = Field(..., min_length=1, max_length=120)
    notes: Optional[str] = None
    calories: int | None = None


class WeekFilter(BaseModel):
    year: int = Field(..., ge=1, le=9999)
    week: int = Field(..., ge=1, le=53)


class DuplicateWeekRequest(BaseModel):
    source: WeekFilter
    target: WeekFilter


# function `validate_iso_date(s: str) -> bool` that returns True if s matches YYYY-MM-DD
def validate_iso_date(s: str) -> bool:
    try:
        date.fromisoformat(s)
        return True
    except ValueError:
        return False
    

# function `validate_email(s: str) -> bool` (we'll need it later for sharing)
import re


def validate_email(s: str) -> bool:
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, s) is not None