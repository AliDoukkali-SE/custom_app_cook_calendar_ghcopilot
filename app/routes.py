from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from typing import List
from uuid import UUID

from .models import Meal, MealCreate, MealUpdate
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
async def create_meal(meal: MealCreate, store: MealStore = Depends(get_store)):
    try:
        return await store.create(Meal(**meal.model_dump()))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/duplicate-week", response_model=List[Meal], status_code=status.HTTP_201_CREATED)
async def duplicate_week(payload: dict, store: MealStore = Depends(get_store)):
    try:
        source = payload["source"]
        target = payload["target"]
        return await store.duplicate_week(
            source_year=int(source["year"]),
            source_week=int(source["week"]),
            target_year=int(target["year"]),
            target_week=int(target["week"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="Invalid payload for duplicate-week") from exc


@router.put("/{meal_id}", response_model=Meal)
async def update_meal(meal_id: UUID, meal: MealUpdate, store: MealStore = Depends(get_store)):
    try:
        return await store.update(str(meal_id), Meal(id=meal_id, **meal.model_dump()))
    except ValueError as exc:
        detail = str(exc)
        if "not found" in detail.lower():
            raise HTTPException(status_code=404, detail=detail) from exc
        raise HTTPException(status_code=409, detail=detail) from exc


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal(meal_id: UUID, store: MealStore = Depends(get_store)):
    try:
        await store.delete(str(meal_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


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
