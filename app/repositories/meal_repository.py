from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from ..schemas import Meal


class MealRepository(ABC):
    @abstractmethod
    async def list_by_week(self, year: int, week: int, owner_id: UUID) -> List[Meal]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, meal: Meal) -> Meal:
        raise NotImplementedError

    @abstractmethod
    async def update(self, meal_id: str, meal: Meal, owner_id: UUID) -> Meal:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, meal_id: str, owner_id: UUID) -> None:
        raise NotImplementedError


class JsonMealRepository(MealRepository):
    def __init__(self, file_path: str = "data/meals.json") -> None:
        self.file_path = file_path
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as stream:
                json.dump([], stream)

    def _read_all(self) -> List[Meal]:
        with open(self.file_path, "r", encoding="utf-8") as stream:
            meals_data = json.load(stream)
        return [Meal(**meal) for meal in meals_data]

    def _write_all(self, meals: List[Meal]) -> None:
        with open(self.file_path, "w", encoding="utf-8") as stream:
            json.dump([meal.model_dump(mode="json") for meal in meals], stream, indent=2)

    async def list_by_week(self, year: int, week: int, owner_id: UUID) -> List[Meal]:
        meals = self._read_all()
        return [
            meal
            for meal in meals
            if meal.date.isocalendar()[:2] == (year, week) and meal.owner_id == owner_id
        ]

    async def create(self, meal: Meal) -> Meal:
        meals = self._read_all()
        meals.append(meal)
        self._write_all(meals)
        return meal

    async def update(self, meal_id: str, meal: Meal, owner_id: UUID) -> Meal:
        meals = self._read_all()
        for index, existing in enumerate(meals):
            if str(existing.id) == meal_id and existing.owner_id == owner_id:
                meal.id = existing.id
                meal.owner_id = owner_id
                meals[index] = meal
                self._write_all(meals)
                return meal
        raise ValueError(f"Meal with id {meal_id} not found")

    async def delete(self, meal_id: str, owner_id: UUID) -> None:
        meals = self._read_all()
        updated = [meal for meal in meals if not (str(meal.id) == meal_id and meal.owner_id == owner_id)]
        if len(updated) == len(meals):
            raise ValueError(f"Meal with id {meal_id} not found")
        self._write_all(updated)
