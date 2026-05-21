from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from .models import Meal
from .storage import MealStore, JsonFileStore

router = APIRouter(prefix="/meals", tags=["meals"])


def get_store() -> MealStore:
    return JsonFileStore()


@router.get("/", response_model=List[Meal])
async def list_meals(year: int, week: int, store: MealStore = Depends(get_store)):
    return await store.list_by_week(year, week)


@router.post("/", response_model=Meal, status_code=status.HTTP_201_CREATED)
async def create_meal(meal: Meal, store: MealStore = Depends(get_store)):
    return await store.create(meal)


@router.put("/{meal_id}", response_model=Meal)
async def update_meal(meal_id: UUID, meal: Meal, store: MealStore = Depends(get_store)):
    return await store.update(str(meal_id), meal)


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal(meal_id: UUID, store: MealStore = Depends(get_store)):
    await store.delete(str(meal_id))
