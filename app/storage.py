# Abstract base `MealStore` with async methods: list_by_week(year, week), create(meal), update(id, meal), delete(id)
# Concrete `JsonFileStore(MealStore)` reading/writing data/meals.json (create file if missing)

from abc import ABC, abstractmethod
from typing import List
from .models import Meal
import json
import os
class MealStore(ABC):
    @abstractmethod
    async def list_by_week(self, year: int, week: int) -> List[Meal]:
        pass

    @abstractmethod
    async def create(self, meal: Meal) -> Meal:
        pass

    @abstractmethod
    async def update(self, id: str, meal: Meal) -> Meal:
        pass

    @abstractmethod
    async def delete(self, id: str) -> None:
        pass
    
class JsonFileStore(MealStore):
    def __init__(self, file_path: str = "data/meals.json"):
        self.file_path = file_path
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump([], f)

    def _read_all(self) -> List[Meal]:
        with open(self.file_path, "r") as f:
            meals_data = json.load(f)
        return [Meal(**meal) for meal in meals_data]

    def _write_all(self, meals: List[Meal]) -> None:
        with open(self.file_path, "w") as f:
            json.dump([meal.model_dump(mode="json") for meal in meals], f, indent=2)

    async def list_by_week(self, year: int, week: int) -> List[Meal]:
        meals = self._read_all()
        return [meal for meal in meals if meal.date.isocalendar()[:2] == (year, week)]

    async def create(self, meal: Meal) -> Meal:
        meals = self._read_all()
        meals.append(meal)
        self._write_all(meals)
        return meal

    async def update(self, id: str, meal: Meal) -> Meal:
        meals = self._read_all()
        for i, existing in enumerate(meals):
            if str(existing.id) == id:
                meal.id = existing.id
                meals[i] = meal
                self._write_all(meals)
                return meal
        raise ValueError(f"Meal with id {id} not found")

    async def delete(self, id: str) -> None:
        meals = self._read_all()
        updated = [m for m in meals if str(m.id) != id]
        if len(updated) == len(meals):
            raise ValueError(f"Meal with id {id} not found")
        self._write_all(updated)