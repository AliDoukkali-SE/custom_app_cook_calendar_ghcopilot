from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List
from uuid import UUID

from .models import Meal, WeekFilter
from .storage import MealStore, JsonFileStore

router = APIRouter(prefix="/meals", tags=["meals"])


async def get_store() -> MealStore:
    return JsonFileStore()


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


@router.get("/", response_model=List[Meal])
async def list_meals(
    week_filter: WeekFilter = Depends(get_week_filter),
    store: MealStore = Depends(get_store),
):
    return await store.list_by_week(week_filter.year, week_filter.week)


@router.post("/", response_model=Meal, status_code=status.HTTP_201_CREATED)
async def create_meal(meal: Meal, store: MealStore = Depends(get_store)):
    return await store.create(meal)


@router.put("/{meal_id}", response_model=Meal)
async def update_meal(meal_id: UUID, meal: Meal, store: MealStore = Depends(get_store)):
    try:
        return await store.update(str(meal_id), meal)
    except ValueError:
        raise HTTPException(status_code=404, detail="Meal not found")


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal(meal_id: UUID, store: MealStore = Depends(get_store)):
    try:
        await store.delete(str(meal_id))
    except ValueError:
        raise HTTPException(status_code=404, detail="Meal not found")
