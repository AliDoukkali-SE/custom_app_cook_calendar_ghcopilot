from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from datetime import date, timedelta
from urllib.parse import urlparse
from uuid import UUID

from azure.core.credentials import AzureNamedKeyCredential, TokenCredential
from azure.data.tables import TableClient, TableServiceClient

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


class CosmosTableStore(MealStore):
	def __init__(
		self,
		endpoint: str,
		key: str | None = None,
		table_name: str = "meals",
		table_client: TableClient | None = None,
		credential: TokenCredential | None = None,
	) -> None:
		self.table_name = table_name
		if table_client:
			self.table = table_client
			return

		if credential is None:
			if not key:
				raise ValueError("CosmosTableStore requires either a key or a TokenCredential")
			hostname = urlparse(endpoint).hostname or ""
			account_name = hostname.split(".")[0]
			credential = AzureNamedKeyCredential(name=account_name, key=key)

		service = TableServiceClient(endpoint=endpoint, credential=credential)
		self.table = service.get_table_client(table_name=table_name)

	@staticmethod
	def _escape_odata(value: str) -> str:
		return value.replace("'", "''")

	@staticmethod
	def _partition_key(year: int, week: int) -> str:
		return f"{year}-W{week:02d}"

	def _partition_key_for_date(self, meal_date: date) -> str:
		year, week, _ = meal_date.isocalendar()
		return self._partition_key(year, week)

	def _meal_to_entity(self, meal: Meal) -> dict:
		return {
			"PartitionKey": self._partition_key_for_date(meal.date),
			"RowKey": str(meal.id),
			"date": meal.date.isoformat(),
			"slot": meal.slot,
			"name": meal.name,
			"notes": meal.notes,
			"calories": meal.calories,
			"ingredients": json.dumps(
				[ingredient.model_dump(mode="json") for ingredient in meal.ingredients],
				ensure_ascii=False,
			),
		}

	def _entity_to_meal(self, entity: dict) -> Meal:
		ingredients_raw = entity.get("ingredients") or "[]"
		if isinstance(ingredients_raw, str):
			ingredients = json.loads(ingredients_raw)
		else:
			ingredients = ingredients_raw

		return Meal(
			id=UUID(entity["RowKey"]),
			date=date.fromisoformat(entity["date"]),
			slot=entity["slot"],
			name=entity["name"],
			notes=entity.get("notes"),
			calories=entity.get("calories"),
			ingredients=ingredients,
		)

	def _query_week_entities(self, year: int, week: int) -> list[dict]:
		partition = self._partition_key(year, week)
		filter_expr = f"PartitionKey eq '{self._escape_odata(partition)}'"
		return list(self.table.query_entities(query_filter=filter_expr))

	def _find_entity_by_id(self, meal_id: str) -> dict | None:
		filter_expr = f"RowKey eq '{self._escape_odata(meal_id)}'"
		matches = list(self.table.query_entities(query_filter=filter_expr))
		return matches[0] if matches else None

	async def list_by_week(self, year: int, week: int) -> list[Meal]:
		entities = self._query_week_entities(year, week)
		return [self._entity_to_meal(entity) for entity in entities]

	async def create(self, meal: Meal) -> Meal:
		year, week, _ = meal.date.isocalendar()
		for entity in self._query_week_entities(year, week):
			if entity.get("date") == meal.date.isoformat() and entity.get("slot") == meal.slot:
				raise ValueError("A meal already exists for this date and slot")

		self.table.create_entity(entity=self._meal_to_entity(meal))
		return meal

	async def update(self, meal_id: str, meal: Meal) -> Meal:
		existing = self._find_entity_by_id(meal_id)
		if not existing:
			raise ValueError(f"Meal with id {meal_id} not found")

		updated_meal = Meal(id=UUID(meal_id), **meal.model_dump(exclude={"id"}))
		target_year, target_week, _ = updated_meal.date.isocalendar()
		for entity in self._query_week_entities(target_year, target_week):
			if entity.get("RowKey") != meal_id and entity.get("date") == updated_meal.date.isoformat() and entity.get("slot") == updated_meal.slot:
				raise ValueError("A meal already exists for this date and slot")

		entity = self._meal_to_entity(updated_meal)
		if existing["PartitionKey"] != entity["PartitionKey"]:
			self.table.delete_entity(partition_key=existing["PartitionKey"], row_key=existing["RowKey"])
			self.table.create_entity(entity=entity)
		else:
			self.table.upsert_entity(mode="Replace", entity=entity)

		return updated_meal

	async def delete(self, meal_id: str) -> None:
		existing = self._find_entity_by_id(meal_id)
		if not existing:
			raise ValueError(f"Meal with id {meal_id} not found")

		self.table.delete_entity(partition_key=existing["PartitionKey"], row_key=existing["RowKey"])

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


def create_store_from_env() -> MealStore:
	endpoint = os.getenv("COSMOS_TABLE_ENDPOINT")
	key = os.getenv("COSMOS_KEY")
	table_name = os.getenv("COSMOS_TABLE_NAME", "meals")

	if endpoint and key:
		return CosmosTableStore(endpoint=endpoint, key=key, table_name=table_name)

	if endpoint:
		# No key provided: use Microsoft Entra ID (managed identity in Azure,
		# developer credentials locally) via DefaultAzureCredential.
		from azure.identity import DefaultAzureCredential

		return CosmosTableStore(
			endpoint=endpoint,
			table_name=table_name,
			credential=DefaultAzureCredential(),
		)

	return JsonFileStore()


__all__ = ["MealStore", "JsonFileStore", "CosmosTableStore", "create_store_from_env"]
