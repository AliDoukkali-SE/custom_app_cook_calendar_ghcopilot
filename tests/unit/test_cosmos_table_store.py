from datetime import date
from unittest.mock import MagicMock

import pytest

from app.models import Meal
from app.storage import CosmosTableStore, JsonFileStore, create_store_from_env


@pytest.mark.anyio
class TestCosmosTableStore:
    async def test_list_by_week_uses_partition_key_and_maps_entities(self):
        table = MagicMock()
        table.query_entities.return_value = [
            {
                "PartitionKey": "2026-W21",
                "RowKey": "550e8400-e29b-41d4-a716-446655440000",
                "date": "2026-05-18",
                "slot": "lunch",
                "name": "Poulet",
                "notes": "Avec riz",
                "calories": 650,
                "ingredients": "[]",
            }
        ]

        store = CosmosTableStore(
            endpoint="https://example.table.cosmos.azure.com:443/",
            key="fake-key",
            table_client=table,
        )

        meals = await store.list_by_week(2026, 21)

        assert len(meals) == 1
        assert meals[0].name == "Poulet"
        table.query_entities.assert_called_once_with(query_filter="PartitionKey eq '2026-W21'")

    async def test_create_rejects_duplicate_date_and_slot(self):
        table = MagicMock()
        table.query_entities.return_value = [
            {
                "PartitionKey": "2026-W21",
                "RowKey": "11111111-1111-1111-1111-111111111111",
                "date": "2026-05-18",
                "slot": "lunch",
                "name": "Existing",
                "ingredients": "[]",
            }
        ]
        store = CosmosTableStore(
            endpoint="https://example.table.cosmos.azure.com:443/",
            key="fake-key",
            table_client=table,
        )

        meal = Meal(date=date(2026, 5, 18), slot="lunch", name="New")

        with pytest.raises(ValueError, match="already exists"):
            await store.create(meal)

        table.create_entity.assert_not_called()

    async def test_create_persists_entity_with_partition_and_row_key(self):
        table = MagicMock()
        table.query_entities.return_value = []
        store = CosmosTableStore(
            endpoint="https://example.table.cosmos.azure.com:443/",
            key="fake-key",
            table_client=table,
        )

        meal = Meal(date=date(2026, 5, 20), slot="dinner", name="Saumon")
        await store.create(meal)

        assert table.create_entity.call_count == 1
        entity = table.create_entity.call_args.kwargs["entity"]
        assert entity["PartitionKey"] == "2026-W21"
        assert entity["RowKey"] == str(meal.id)

    async def test_update_moves_entity_when_week_changes(self):
        table = MagicMock()

        def query_side_effect(*, query_filter: str):
            if "RowKey eq" in query_filter:
                return [
                    {
                        "PartitionKey": "2026-W21",
                        "RowKey": "550e8400-e29b-41d4-a716-446655440000",
                        "date": "2026-05-18",
                        "slot": "lunch",
                        "name": "Old",
                        "ingredients": "[]",
                    }
                ]
            if "PartitionKey eq '2026-W22'" in query_filter:
                return []
            return []

        table.query_entities.side_effect = query_side_effect

        store = CosmosTableStore(
            endpoint="https://example.table.cosmos.azure.com:443/",
            key="fake-key",
            table_client=table,
        )

        updated = Meal(
            date=date(2026, 5, 26),
            slot="lunch",
            name="Updated",
        )

        result = await store.update("550e8400-e29b-41d4-a716-446655440000", updated)

        assert result.name == "Updated"
        table.delete_entity.assert_called_once_with(
            partition_key="2026-W21",
            row_key="550e8400-e29b-41d4-a716-446655440000",
        )
        assert table.create_entity.call_count == 1


class TestCreateStoreFromEnv:
    def test_fallbacks_to_json_store_when_env_missing(self, monkeypatch):
        monkeypatch.delenv("COSMOS_TABLE_ENDPOINT", raising=False)
        monkeypatch.delenv("COSMOS_KEY", raising=False)

        store = create_store_from_env()

        assert isinstance(store, JsonFileStore)
