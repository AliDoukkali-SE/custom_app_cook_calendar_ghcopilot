from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from typing import List
from uuid import UUID

from .models import DuplicateWeekRequest, Meal, MealCreate, MealUpdate, WeekFilter
from .storage import MealStore, JsonFileStore

router = APIRouter(prefix="/meals", tags=["meals"])


async def get_store() -> MealStore:
    return JsonFileStore()


async def get_owner_id(x_user_id: str = Header(...)) -> UUID:
    """Extract owner_id from X-User-Id header"""
    try:
        return UUID(x_user_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="X-User-Id header must be a valid UUID",
        )


async def get_week_filter(
    year: int = Query(..., ge=1, le=9999),
    week: int = Query(..., ge=1, le=53),
) -> WeekFilter:
    max_week_for_year = date(year, 12, 28).isocalendar().week
    if week > max_week_for_year:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid ISO week {week} for year {year}. Max is {max_week_for_year}.",
        )
    return WeekFilter(year=year, week=week)


def validate_week_filter(week_filter: WeekFilter) -> None:
    max_week_for_year = date(week_filter.year, 12, 28).isocalendar().week
    if week_filter.week > max_week_for_year:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid ISO week {week_filter.week} for year {week_filter.year}. "
                f"Max is {max_week_for_year}."
            ),
        )


@router.get("/", response_model=List[Meal])
async def list_meals(
    week_filter: WeekFilter = Depends(get_week_filter),
    owner_id: UUID = Depends(get_owner_id),
    store: MealStore = Depends(get_store),
):
    return await store.list_by_week(week_filter.year, week_filter.week, owner_id)


@router.post("/", response_model=Meal, status_code=status.HTTP_201_CREATED)
async def create_meal(
    meal_data: MealCreate,
    owner_id: UUID = Depends(get_owner_id),
    store: MealStore = Depends(get_store),
):
    meal = Meal(**meal_data.model_dump(), owner_id=owner_id)
    return await store.create(meal)


@router.post("/duplicate-week", response_model=List[Meal], status_code=status.HTTP_201_CREATED)
async def duplicate_week(
    payload: DuplicateWeekRequest,
    owner_id: UUID = Depends(get_owner_id),
    store: MealStore = Depends(get_store),
):
    validate_week_filter(payload.source)
    validate_week_filter(payload.target)

    source_monday = date.fromisocalendar(payload.source.year, payload.source.week, 1)
    target_monday = date.fromisocalendar(payload.target.year, payload.target.week, 1)
    day_delta = (target_monday - source_monday).days

    source_meals = await store.list_by_week(payload.source.year, payload.source.week, owner_id)

    duplicated_meals: List[Meal] = []
    for source_meal in source_meals:
        duplicated_meal = Meal(
            date=source_meal.date + timedelta(days=day_delta),
            slot=source_meal.slot,
            name=source_meal.name,
            notes=source_meal.notes,
            calories=source_meal.calories,
            owner_id=owner_id,
        )
        duplicated_meals.append(await store.create(duplicated_meal))

    return duplicated_meals


@router.put("/{meal_id}", response_model=Meal)
async def update_meal(
    meal_id: UUID,
    meal_data: MealUpdate,
    owner_id: UUID = Depends(get_owner_id),
    store: MealStore = Depends(get_store),
):
    try:
        meal = Meal(**meal_data.model_dump(), id=meal_id, owner_id=owner_id)
        return await store.update(str(meal_id), meal, owner_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Meal not found")


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal(
    meal_id: UUID,
    owner_id: UUID = Depends(get_owner_id),
    store: MealStore = Depends(get_store),
):
    try:
        await store.delete(str(meal_id), owner_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Meal not found")
