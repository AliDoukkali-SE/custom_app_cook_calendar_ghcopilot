from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from typing import List
from uuid import UUID

from .models import Meal
from .storage import MealStore, JsonFileStore
from .shopping import aggregate_ingredients, generate_txt

router = APIRouter(prefix="/meals", tags=["meals"])
shopping_router = APIRouter(prefix="/shopping-list", tags=["shopping"])


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


@shopping_router.get("/")
async def get_shopping_list(
    year: int,
    week: int,
    format: str | None = None,
    store: MealStore = Depends(get_store),
):
    meals = await store.list_by_week(year, week)
    categories = aggregate_ingredients(meals)

    if format == "txt":
        content = generate_txt(year, week, categories)
        filename = f"liste-courses-semaine-{week}-{year}.txt"
        return PlainTextResponse(
            content=content,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    return {"year": year, "week": week, "categories": categories}
