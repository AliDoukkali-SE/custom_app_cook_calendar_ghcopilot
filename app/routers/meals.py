from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..dependencies import get_owner_id, get_repository, get_service
from ..repositories import MealRepository
from ..schemas import DuplicateWeekRequest, Meal, MealCreate, MealUpdate, WeekFilter
from ..services import MealConflictError, MealNotFoundError, MealService

router = APIRouter(prefix="/meals", tags=["meals"])


async def get_week_filter(
    year: int = Query(..., ge=1, le=9999),
    week: int = Query(..., ge=1, le=53),
) -> WeekFilter:
    return WeekFilter(year=year, week=week)


async def service_dependency(repository: MealRepository = Depends(get_repository)) -> MealService:
    return await get_service(repository)


@router.get("/", response_model=List[Meal])
async def list_meals(
    week_filter: WeekFilter = Depends(get_week_filter),
    owner_id: UUID = Depends(get_owner_id),
    service: MealService = Depends(service_dependency),
):
    try:
        return await service.list_meals(week_filter, owner_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/", response_model=Meal, status_code=status.HTTP_201_CREATED)
async def create_meal(
    meal_data: MealCreate,
    owner_id: UUID = Depends(get_owner_id),
    service: MealService = Depends(service_dependency),
):
    try:
        return await service.create_meal(meal_data, owner_id)
    except MealConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/duplicate-week", response_model=List[Meal], status_code=status.HTTP_201_CREATED)
async def duplicate_week(
    payload: DuplicateWeekRequest,
    owner_id: UUID = Depends(get_owner_id),
    service: MealService = Depends(service_dependency),
):
    try:
        return await service.duplicate_week(payload, owner_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except MealConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.put("/{meal_id}", response_model=Meal)
async def update_meal(
    meal_id: UUID,
    meal_data: MealUpdate,
    owner_id: UUID = Depends(get_owner_id),
    service: MealService = Depends(service_dependency),
):
    try:
        return await service.update_meal(meal_id, meal_data, owner_id)
    except MealNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Meal not found") from exc
    except MealConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal(
    meal_id: UUID,
    owner_id: UUID = Depends(get_owner_id),
    service: MealService = Depends(service_dependency),
):
    try:
        await service.delete_meal(meal_id, owner_id)
    except MealNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Meal not found") from exc
