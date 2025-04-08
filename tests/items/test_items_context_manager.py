import pytest

from dankmemer import DankMemerClient, Fuzzy, ItemsFilter


@pytest.mark.asyncio
async def test_items_query_context_manager():
    sample_data = {
        "1": {
            "id": 1,
            "name": "Trash",
            "details": "Used trash bags",
            "emoji": "<:Trash:986723862190383165>",
            "flavor": "I think I’m done buying trash bags...",
            "hasUse": False,
            "imageURL": "http://example.com/trash.png",
            "itemKey": "trash",
            "marketValue": 1000,
            "netValue": 100,
            "rarity": "Common",
            "skins": {},
            "tags": {},
            "type": "Sellable",
            "value": 100,
        },
        "2": {
            "id": 2,
            "name": "Worm",
            "details": "A squirming worm",
            "emoji": "<:Worm:864261394920898600>",
            "flavor": "A tiny worm",
            "hasUse": True,
            "imageURL": "http://example.com/worm.png",
            "itemKey": "worm",
            "marketValue": 2000,
            "netValue": 200,
            "rarity": "Common",
            "skins": {},
            "tags": {},
            "type": "Sellable",
            "value": 200,
        },
    }

    async def dummy_request(route: str, params: dict = None):
        return sample_data

    async with DankMemerClient(cache_ttl_hours=1) as client:
        client.request = dummy_request

        # Test without filter
        result = await client.items.query()
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].name == "Trash"

        # Test with fuzzy filtering using Fuzzy for the 'name' field
        filter_obj = ItemsFilter(name=Fuzzy("trash", cutoff=70))
        fuzzy_result = await client.items.query(filter_obj)
        # Only "Trash" should match (case-insensitive fuzzy matching)
        assert len(fuzzy_result) == 1
        assert fuzzy_result[0].name.lower().find("trash") != -1
