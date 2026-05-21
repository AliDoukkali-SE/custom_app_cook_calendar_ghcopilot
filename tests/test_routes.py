from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models import Meal
from app.routes import get_store
from app.storage import JsonFileStore, MealStore


@pytest.fixture
def json_store(tmp_path):
    data_file = tmp_path / "meals.json"
    return JsonFileStore(file_path=str(data_file))


@pytest.fixture
def test_app(json_store):
    app.dependency_overrides[get_store] = lambda: json_store
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def client(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest.mark.anyio
class TestMealsRoutesCRUD:
    async def test_create_and_list_meal(self, client: AsyncClient):
        payload = {
            "date": "2026-01-06",
            "slot": "lunch",
            "name": "Poulet curry",
            "notes": "Avec du riz",
            "calories": 650,
        }

        create_response = await client.post("/meals/", json=payload)
        assert create_response.status_code == 201

        created = create_response.json()
        assert created["id"]
        assert created["date"] == payload["date"]
        assert created["slot"] == payload["slot"]
        assert created["name"] == payload["name"]
        assert created["notes"] == payload["notes"]
        assert created["calories"] == payload["calories"]

        iso_year, iso_week, _ = date.fromisoformat(payload["date"]).isocalendar()
        list_response = await client.get(f"/meals/?year={iso_year}&week={iso_week}")

        assert list_response.status_code == 200
        meals = list_response.json()
        assert len(meals) == 1
        assert meals[0]["id"] == created["id"]

    async def test_update_meal(self, client: AsyncClient):
        create_payload = {
            "date": "2026-02-10",
            "slot": "dinner",
            "name": "Pates",
            "notes": None,
            "calories": 500,
        }
        create_response = await client.post("/meals/", json=create_payload)
        meal_id = create_response.json()["id"]

        update_payload = {
            "date": "2026-02-10",
            "slot": "dinner",
            "name": "Pates bolognaise",
            "notes": "Parmesan",
            "calories": 780,
        }
        update_response = await client.put(f"/meals/{meal_id}", json=update_payload)

        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["id"] == meal_id
        assert updated["name"] == "Pates bolognaise"
        assert updated["notes"] == "Parmesan"
        assert updated["calories"] == 780

    async def test_delete_meal(self, client: AsyncClient):
        payload = {
            "date": "2026-03-03",
            "slot": "breakfast",
            "name": "Porridge",
            "notes": "Banane",
            "calories": 390,
        }
        create_response = await client.post("/meals/", json=payload)
        meal_id = create_response.json()["id"]

        delete_response = await client.delete(f"/meals/{meal_id}")
        assert delete_response.status_code == 204

        iso_year, iso_week, _ = date.fromisoformat(payload["date"]).isocalendar()
        list_response = await client.get(f"/meals/?year={iso_year}&week={iso_week}")

        assert list_response.status_code == 200
        assert list_response.json() == []

    async def test_update_and_delete_unknown_meal_return_404(self, client: AsyncClient):
        missing_id = "9f749f39-b1d6-4941-b803-3ecb66ea5c9f"
        payload = {
            "date": "2026-04-01",
            "slot": "lunch",
            "name": "Salade",
            "notes": None,
            "calories": 300,
        }

        update_response = await client.put(f"/meals/{missing_id}", json=payload)
        assert update_response.status_code == 404
        assert update_response.json()["detail"] == "Meal not found"

        delete_response = await client.delete(f"/meals/{missing_id}")
        assert delete_response.status_code == 404
        assert delete_response.json()["detail"] == "Meal not found"

    async def test_list_meals_rejects_invalid_week_for_year(self, client: AsyncClient):
        response = await client.get("/meals/?year=2021&week=53")

        assert response.status_code == 422
        assert "Invalid ISO week" in response.json()["detail"]


@pytest.mark.anyio
async def test_post_meals_calls_store_create_once():
    payload = {
        "date": "2026-05-15",
        "slot": "lunch",
        "name": "Wrap poulet",
        "notes": "Sauce yaourt",
        "calories": 560,
    }
    meal_to_return = Meal(**payload)

    mocked_store = MagicMock(spec=MealStore)
    mocked_store.create = AsyncMock(return_value=meal_to_return)

    app.dependency_overrides[get_store] = lambda: mocked_store
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/meals/", json=payload)

        assert response.status_code == 201
        mocked_store.create.assert_awaited_once()
        created_meal_arg = mocked_store.create.await_args.args[0]
        assert isinstance(created_meal_arg, Meal)
        assert created_meal_arg.name == payload["name"]
        assert created_meal_arg.slot == payload["slot"]
    finally:
        app.dependency_overrides.clear()