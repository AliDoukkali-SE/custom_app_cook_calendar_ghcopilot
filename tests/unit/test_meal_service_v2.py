from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from app.schemas import DuplicateWeekRequest, Meal, MealCreate, MealUpdate, WeekFilter
from app.services import MealConflictError, MealNotFoundError, MealService

TEST_OWNER_ID = UUID("550e8400-e29b-41d4-a716-446655440000")


@pytest.mark.anyio
async def test_create_meal_rejects_same_date_and_slot_for_same_owner():
    repository = MagicMock()
    repository.list_by_week = AsyncMock(
        return_value=[
            Meal(
                date=date(2026, 1, 6),
                slot="lunch",
                name="Already planned",
                notes=None,
                calories=500,
                owner_id=TEST_OWNER_ID,
            )
        ]
    )
    repository.create = AsyncMock()

    service = MealService(repository=repository)

    with pytest.raises(MealConflictError):
        await service.create_meal(
            MealCreate(
                date=date(2026, 1, 6),
                slot="lunch",
                name="Should fail",
                notes=None,
                calories=450,
            ),
            TEST_OWNER_ID,
        )


@pytest.mark.anyio
async def test_update_meal_allows_same_slot_when_updating_same_meal():
    meal_id = UUID("83d4de5f-0a29-4f8a-97bf-4e3226d9756e")
    existing = Meal(
        id=meal_id,
        date=date(2026, 1, 6),
        slot="lunch",
        name="Original",
        notes=None,
        calories=450,
        owner_id=TEST_OWNER_ID,
    )

    repository = MagicMock()
    repository.list_by_week = AsyncMock(return_value=[existing])
    repository.update = AsyncMock(return_value=existing)

    service = MealService(repository=repository)
    updated = await service.update_meal(
        meal_id,
        MealUpdate(
            date=date(2026, 1, 6),
            slot="lunch",
            name="Updated",
            notes="new",
            calories=500,
        ),
        TEST_OWNER_ID,
    )

    assert updated.id == meal_id
    repository.update.assert_awaited_once()


@pytest.mark.anyio
async def test_update_unknown_meal_raises_not_found():
    repository = MagicMock()
    repository.list_by_week = AsyncMock(return_value=[])
    repository.update = AsyncMock(side_effect=ValueError("not found"))

    service = MealService(repository=repository)

    with pytest.raises(MealNotFoundError):
        await service.update_meal(
            UUID("a13f1555-536d-48ff-a705-db9dbbc2f2f0"),
            MealUpdate(
                date=date(2026, 2, 10),
                slot="dinner",
                name="Missing",
                notes=None,
                calories=100,
            ),
            TEST_OWNER_ID,
        )


@pytest.mark.anyio
async def test_duplicate_week_duplicates_all_meals_with_shifted_dates():
    source_meals = [
        Meal(
            date=date(2026, 1, 6),
            slot="breakfast",
            name="Omelette",
            notes="Fromage",
            calories=420,
            owner_id=TEST_OWNER_ID,
        ),
        Meal(
            date=date(2026, 1, 8),
            slot="dinner",
            name="Saumon",
            notes="Legumes",
            calories=610,
            owner_id=TEST_OWNER_ID,
        ),
    ]

    repository = MagicMock()
    repository.list_by_week = AsyncMock(side_effect=[source_meals, [], []])
    repository.create = AsyncMock(side_effect=lambda meal: meal)

    service = MealService(repository=repository)

    duplicated = await service.duplicate_week(
        DuplicateWeekRequest(
            source=WeekFilter(year=2026, week=2),
            target=WeekFilter(year=2026, week=5),
        ),
        TEST_OWNER_ID,
    )

    assert len(duplicated) == 2
    assert duplicated[0].date.isoformat() == "2026-01-27"
    assert duplicated[1].date.isoformat() == "2026-01-29"


@pytest.mark.anyio
async def test_list_meals_rejects_invalid_week():
    repository = MagicMock()
    repository.list_by_week = AsyncMock(return_value=[])
    service = MealService(repository=repository)

    with pytest.raises(ValueError):
        await service.list_meals(WeekFilter(year=2021, week=53), TEST_OWNER_ID)
