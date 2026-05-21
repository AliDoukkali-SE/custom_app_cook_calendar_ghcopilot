"""Unit tests for shopping list feature."""
import pytest
from datetime import date
from unittest.mock import AsyncMock, patch

from app.models import Ingredient, Meal
from app.shopping import aggregate_ingredients, generate_txt, _format_ingredient_txt


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------

def make_meal(ingredients=None, meal_date=date(2026, 5, 18)):
    return Meal(
        date=meal_date,
        slot="lunch",
        name="Test meal",
        ingredients=ingredients or [],
    )


def make_ingredient(name, quantity=None, unit=None, category="autres"):
    return Ingredient(name=name, quantity=quantity, unit=unit, category=category)


# ---------------------------------------------------------------------------
# aggregate_ingredients — basic aggregation
# ---------------------------------------------------------------------------

class TestAggregateIngredients:
    def test_empty_meals_returns_empty_categories(self):
        result = aggregate_ingredients([])
        assert result == {"légumes": [], "protéines": [], "féculents": [], "autres": []}

    def test_meal_without_ingredients_is_ignored(self):
        meals = [make_meal(ingredients=[])]
        result = aggregate_ingredients(meals)
        for cat in result.values():
            assert cat == []

    def test_single_ingredient_appears_in_correct_category(self):
        ing = make_ingredient("tomates", quantity=3, unit="pièce", category="légumes")
        meals = [make_meal(ingredients=[ing])]
        result = aggregate_ingredients(meals)
        assert len(result["légumes"]) == 1
        assert result["légumes"][0]["name"] == "tomates"
        assert result["légumes"][0]["quantity"] == 3
        assert result["légumes"][0]["unit"] == "pièce"

    def test_same_ingredient_same_unit_are_merged(self):
        ing1 = make_ingredient("tomates", quantity=3, unit="pièce", category="légumes")
        ing2 = make_ingredient("tomates", quantity=2, unit="pièce", category="légumes")
        meals = [make_meal(ingredients=[ing1, ing2])]
        result = aggregate_ingredients(meals)
        assert len(result["légumes"]) == 1
        assert result["légumes"][0]["quantity"] == 5

    def test_same_ingredient_case_insensitive_merged(self):
        ing1 = make_ingredient("Tomates", quantity=3, unit="pièce", category="légumes")
        ing2 = make_ingredient("tomates", quantity=2, unit="pièce", category="légumes")
        meals = [make_meal(ingredients=[ing1]), make_meal(ingredients=[ing2])]
        result = aggregate_ingredients(meals)
        assert len(result["légumes"]) == 1
        assert result["légumes"][0]["quantity"] == 5

    def test_same_ingredient_different_units_listed_separately(self):
        ing1 = make_ingredient("poulet", quantity=500, unit="g", category="protéines")
        ing2 = make_ingredient("poulet", quantity=2, unit="kg", category="protéines")
        meals = [make_meal(ingredients=[ing1, ing2])]
        result = aggregate_ingredients(meals)
        assert len(result["protéines"]) == 2

    def test_ingredients_from_multiple_meals_merged(self):
        meal1 = make_meal(ingredients=[make_ingredient("riz", quantity=200, unit="g", category="féculents")])
        meal2 = make_meal(ingredients=[make_ingredient("riz", quantity=300, unit="g", category="féculents")])
        result = aggregate_ingredients([meal1, meal2])
        assert len(result["féculents"]) == 1
        assert result["féculents"][0]["quantity"] == 500

    def test_ingredient_without_quantity(self):
        ing = make_ingredient("sel", quantity=None, unit=None, category="autres")
        meals = [make_meal(ingredients=[ing])]
        result = aggregate_ingredients(meals)
        assert len(result["autres"]) == 1
        assert result["autres"][0]["quantity"] is None

    def test_all_four_categories_always_present(self):
        result = aggregate_ingredients([])
        assert set(result.keys()) == {"légumes", "protéines", "féculents", "autres"}


# ---------------------------------------------------------------------------
# generate_txt — text export
# ---------------------------------------------------------------------------

class TestGenerateTxt:
    def test_header_contains_week_and_year(self):
        categories = {"légumes": [], "protéines": [], "féculents": [], "autres": []}
        txt = generate_txt(2026, 21, categories)
        assert "Semaine 21 (2026)" in txt

    def test_category_headers_present(self):
        categories = {"légumes": [], "protéines": [], "féculents": [], "autres": []}
        txt = generate_txt(2026, 21, categories)
        assert "## Légumes" in txt
        assert "## Protéines" in txt
        assert "## Féculents" in txt
        assert "## Autres" in txt

    def test_ingredient_with_piece_unit_formatted_as_xN(self):
        categories = {
            "légumes": [{"name": "tomates", "quantity": 6, "unit": "pièce"}],
            "protéines": [],
            "féculents": [],
            "autres": [],
        }
        txt = generate_txt(2026, 21, categories)
        assert "Tomates x6" in txt

    def test_ingredient_with_weight_unit_formatted_correctly(self):
        categories = {
            "légumes": [],
            "protéines": [{"name": "poulet", "quantity": 500, "unit": "g"}],
            "féculents": [],
            "autres": [],
        }
        txt = generate_txt(2026, 21, categories)
        assert "Poulet 500g" in txt

    def test_empty_week_generates_valid_txt(self):
        categories = {"légumes": [], "protéines": [], "féculents": [], "autres": []}
        txt = generate_txt(2026, 21, categories)
        assert "🛒" in txt
        # No ingredients listed but headers should still be there
        assert "## Légumes" in txt

    def test_ingredient_without_quantity_or_unit(self):
        item = {"name": "sel", "quantity": None, "unit": None}
        result = _format_ingredient_txt(item)
        assert result == "- Sel"

    def test_ingredient_with_float_quantity(self):
        item = {"name": "huile", "quantity": 1.5, "unit": "L"}
        result = _format_ingredient_txt(item)
        assert result == "- Huile 1.5L"

    def test_ingredient_integer_quantity_displayed_without_decimal(self):
        item = {"name": "riz", "quantity": 1.0, "unit": "kg"}
        result = _format_ingredient_txt(item)
        assert result == "- Riz 1kg"


# ---------------------------------------------------------------------------
# Integration tests with FastAPI TestClient
# ---------------------------------------------------------------------------

from fastapi.testclient import TestClient
from app.main import app


def _make_store_mock(meals):
    mock = AsyncMock()
    mock.list_by_week = AsyncMock(return_value=meals)
    return mock


class TestShoppingListEndpoint:
    def test_json_response_structure(self):
        meals = [
            make_meal(ingredients=[
                make_ingredient("tomates", 4, "pièce", "légumes"),
                make_ingredient("riz", 200, "g", "féculents"),
            ])
        ]
        from app.routes import get_store
        app.dependency_overrides[get_store] = lambda: _make_store_mock(meals)
        try:
            client = TestClient(app)
            resp = client.get("/shopping-list/?year=2026&week=21")
            assert resp.status_code == 200
            data = resp.json()
            assert data["year"] == 2026
            assert data["week"] == 21
            assert "categories" in data
            assert "légumes" in data["categories"]
        finally:
            app.dependency_overrides.clear()

    def test_empty_week_returns_empty_categories(self):
        from app.routes import get_store
        app.dependency_overrides[get_store] = lambda: _make_store_mock([])
        try:
            client = TestClient(app)
            resp = client.get("/shopping-list/?year=2026&week=99")
            assert resp.status_code == 200
            data = resp.json()
            for cat in ["légumes", "protéines", "féculents", "autres"]:
                assert data["categories"][cat] == []
        finally:
            app.dependency_overrides.clear()

    def test_txt_format_returns_plain_text(self):
        meals = [
            make_meal(ingredients=[
                make_ingredient("tomates", 6, "pièce", "légumes"),
                make_ingredient("poulet", 500, "g", "protéines"),
            ])
        ]
        from app.routes import get_store
        app.dependency_overrides[get_store] = lambda: _make_store_mock(meals)
        try:
            client = TestClient(app)
            resp = client.get("/shopping-list/?year=2026&week=21&format=txt")
            assert resp.status_code == 200
            assert "text/plain" in resp.headers["content-type"]
            assert "attachment" in resp.headers.get("content-disposition", "")
            assert "Semaine 21 (2026)" in resp.text
        finally:
            app.dependency_overrides.clear()

    def test_aggregation_in_endpoint(self):
        meals = [
            make_meal(
                ingredients=[make_ingredient("riz", 200, "g", "féculents")],
                meal_date=date(2026, 5, 18),
            ),
            make_meal(
                ingredients=[make_ingredient("riz", 300, "g", "féculents")],
                meal_date=date(2026, 5, 19),
            ),
        ]
        from app.routes import get_store
        app.dependency_overrides[get_store] = lambda: _make_store_mock(meals)
        try:
            client = TestClient(app)
            resp = client.get("/shopping-list/?year=2026&week=21")
            assert resp.status_code == 200
            data = resp.json()
            fec = data["categories"]["féculents"]
            assert len(fec) == 1
            assert fec[0]["quantity"] == 500
        finally:
            app.dependency_overrides.clear()

    def test_mixed_units_listed_separately(self):
        meals = [
            make_meal(ingredients=[
                make_ingredient("poulet", 500, "g", "protéines"),
                make_ingredient("poulet", 1, "kg", "protéines"),
            ])
        ]
        from app.routes import get_store
        app.dependency_overrides[get_store] = lambda: _make_store_mock(meals)
        try:
            client = TestClient(app)
            resp = client.get("/shopping-list/?year=2026&week=21")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["categories"]["protéines"]) == 2
        finally:
            app.dependency_overrides.clear()
