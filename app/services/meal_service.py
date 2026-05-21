from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from ..repositories import MealRepository
from ..schemas import DuplicateWeekRequest, Meal, MealCreate, MealUpdate, WeekFilter


class MealNotFoundError(Exception):
    pass


class MealConflictError(Exception):
    pass


class MealService:
    def __init__(self, repository: MealRepository) -> None:
        self.repository = repository

    @staticmethod
    def validate_week_filter(week_filter: WeekFilter) -> None:
        max_week_for_year = date(week_filter.year, 12, 28).isocalendar().week
        if week_filter.week > max_week_for_year:
            raise ValueError(
                f"Invalid ISO week {week_filter.week} for year {week_filter.year}. Max is {max_week_for_year}."
            )

    async def list_meals(self, week_filter: WeekFilter, owner_id: UUID) -> list[Meal]:
        self.validate_week_filter(week_filter)
        return await self.repository.list_by_week(week_filter.year, week_filter.week, owner_id)

    async def create_meal(self, meal_data: MealCreate, owner_id: UUID) -> Meal:
        await self._ensure_unique_date_slot(owner_id=owner_id, meal_date=meal_data.date, slot=meal_data.slot)
        meal = Meal(**meal_data.model_dump(), owner_id=owner_id)
        return await self.repository.create(meal)

    async def update_meal(self, meal_id: UUID, meal_data: MealUpdate, owner_id: UUID) -> Meal:
        await self._ensure_unique_date_slot(
            owner_id=owner_id,
            meal_date=meal_data.date,
            slot=meal_data.slot,
            exclude_meal_id=meal_id,
        )
        meal = Meal(**meal_data.model_dump(), id=meal_id, owner_id=owner_id)
        try:
            return await self.repository.update(str(meal_id), meal, owner_id)
        except ValueError as exc:
            raise MealNotFoundError("Meal not found") from exc

    async def delete_meal(self, meal_id: UUID, owner_id: UUID) -> None:
        try:
            await self.repository.delete(str(meal_id), owner_id)
        except ValueError as exc:
            raise MealNotFoundError("Meal not found") from exc

    async def duplicate_week(self, payload: DuplicateWeekRequest, owner_id: UUID) -> list[Meal]:
        self.validate_week_filter(payload.source)
        self.validate_week_filter(payload.target)

        source_monday = date.fromisocalendar(payload.source.year, payload.source.week, 1)
        target_monday = date.fromisocalendar(payload.target.year, payload.target.week, 1)
        day_delta = (target_monday - source_monday).days

        source_meals = await self.repository.list_by_week(payload.source.year, payload.source.week, owner_id)

        duplicated: list[Meal] = []
        for source_meal in source_meals:
            duplicated_data = MealCreate(
                date=source_meal.date + timedelta(days=day_delta),
                slot=source_meal.slot,
                name=source_meal.name,
                notes=source_meal.notes,
                calories=source_meal.calories,
            )
            duplicated.append(await self.create_meal(duplicated_data, owner_id))

        return duplicated

    async def _ensure_unique_date_slot(
        self,
        owner_id: UUID,
        meal_date: date,
        slot: str,
        exclude_meal_id: UUID | None = None,
    ) -> None:
        year, week, _ = meal_date.isocalendar()
        meals = await self.repository.list_by_week(year, week, owner_id)

        for meal in meals:
            if exclude_meal_id is not None and meal.id == exclude_meal_id:
                continue
            if meal.date == meal_date and meal.slot == slot:
                raise MealConflictError("A meal already exists for this owner/date/slot")
