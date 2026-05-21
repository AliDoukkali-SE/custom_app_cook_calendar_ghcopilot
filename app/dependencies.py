from __future__ import annotations

from uuid import UUID

from fastapi import Header, HTTPException

from .repositories import JsonMealRepository, MealRepository
from .services import MealService


async def get_store() -> MealRepository:
    return JsonMealRepository()


# Backward-compatible alias used by v2 tests.
get_repository = get_store


async def get_service(repository: MealRepository = None) -> MealService:
    repo = repository or await get_store()
    return MealService(repository=repo)


async def get_owner_id(x_user_id: str = Header(...)) -> UUID:
    try:
        return UUID(x_user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="X-User-Id header must be a valid UUID",
        ) from exc
