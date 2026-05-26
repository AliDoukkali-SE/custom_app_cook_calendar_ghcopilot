from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from datetime import date, timedelta

from .models import Meal


class MealStore(ABC):
	@abstractmethod
	async def list_by_week(self, year: int, week: int) -> list[Meal]:
		raise NotImplementedError

	@abstractmethod
	async def create(self, meal: Meal) -> Meal:
		raise NotImplementedError

	@abstractmethod
	async def update(self, meal_id: str, meal: Meal) -> Meal:
		raise NotImplementedError

	@abstractmethod
	async def delete(self, meal_id: str) -> None:
		raise NotImplementedError

	@abstractmethod
	async def duplicate_week(self, source_year: int, source_week: int, target_year: int, target_week: int) -> list[Meal]:
		raise NotImplementedError


class JsonFileStore(MealStore):
	def __init__(self, file_path: str = "data/meals.json") -> None:
		self.file_path = file_path
		os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
		if not os.path.exists(self.file_path):
			with open(self.file_path, "w", encoding="utf-8") as stream:
				json.dump([], stream)

	def _read_all(self) -> list[Meal]:
		with open(self.file_path, "r", encoding="utf-8") as stream:
			data = json.load(stream)
		return [Meal(**item) for item in data]

	def _write_all(self, meals: list[Meal]) -> None:
		with open(self.file_path, "w", encoding="utf-8") as stream:
			json.dump([meal.model_dump(mode="json") for meal in meals], stream, ensure_ascii=False, indent=2)

	async def list_by_week(self, year: int, week: int) -> list[Meal]:
		meals = self._read_all()
		return [meal for meal in meals if meal.date.isocalendar()[:2] == (year, week)]

	async def create(self, meal: Meal) -> Meal:
		meals = self._read_all()
		for existing in meals:
			if existing.date == meal.date and existing.slot == meal.slot:
				raise ValueError("A meal already exists for this date and slot")
		meals.append(meal)
		self._write_all(meals)
		return meal

	async def update(self, meal_id: str, meal: Meal) -> Meal:
		meals = self._read_all()
		for idx, existing in enumerate(meals):
			if str(existing.id) != meal_id and existing.date == meal.date and existing.slot == meal.slot:
				raise ValueError("A meal already exists for this date and slot")
		for idx, existing in enumerate(meals):
			if str(existing.id) == meal_id:
				meals[idx] = Meal(id=existing.id, **meal.model_dump(exclude={"id"}))
				self._write_all(meals)
				return meals[idx]
		raise ValueError(f"Meal with id {meal_id} not found")

	async def delete(self, meal_id: str) -> None:
		meals = self._read_all()
		updated = [meal for meal in meals if str(meal.id) != meal_id]
		if len(updated) == len(meals):
			raise ValueError(f"Meal with id {meal_id} not found")
		self._write_all(updated)

	async def duplicate_week(self, source_year: int, source_week: int, target_year: int, target_week: int) -> list[Meal]:
		source_meals = await self.list_by_week(source_year, source_week)
		source_monday = date.fromisocalendar(source_year, source_week, 1)
		target_monday = date.fromisocalendar(target_year, target_week, 1)
		day_delta = (target_monday - source_monday).days

		duplicated: list[Meal] = []
		for meal in source_meals:
			duplicated_meal = Meal(
				date=meal.date + timedelta(days=day_delta),
				slot=meal.slot,
				name=meal.name,
				notes=meal.notes,
				calories=meal.calories,
				ingredients=meal.ingredients,
			)
			duplicated.append(await self.create(duplicated_meal))

		return duplicated


__all__ = ["MealStore", "JsonFileStore"]
