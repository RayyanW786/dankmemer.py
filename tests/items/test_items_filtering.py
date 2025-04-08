import pytest

from dankmemer import DankMemerClient, Fuzzy, ItemsFilter


@pytest.mark.asyncio
async def test_items_advanced_filtering():
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
            "marketValue": 9603000,
            "netValue": 100,
            "rarity": "Uncommon",
            "skins": {},
            "tags": {},
            "type": "Sellable",
            "value": 100,
        },
        "2": {
            "id": 2,
            "name": "Worm",
            "details": "A tiny worm",
            "emoji": "<:Worm:864261394920898600>",
            "flavor": "A small worm indeed",
            "hasUse": False,
            "imageURL": "http://example.com/worm.png",
            "itemKey": "worm",
            "marketValue": 21000,
            "netValue": 200,
            "rarity": "Common",
            "skins": {},
            "tags": {},
            "type": "Sellable",
            "value": 200,
        },
        "3": {
            "id": 3,
            "name": "Wedding Gift",
            "details": "A beautiful gift",
            "emoji": "<:WeddingGift:877566903516790855>",
            "flavor": "Now you have to write thank you notes...",
            "hasUse": True,
            "imageURL": "http://example.com/wedding.png",
            "itemKey": "weddinggift",
            "marketValue": 5534000,
            "netValue": 500000,
            "rarity": "Rare",
            "skins": {},
            "tags": {},
            "type": "Loot Box",
            "value": 500000,
        },
    }

    async def dummy_request(route: str, params: dict = None):
        return sample_data

    client = DankMemerClient(cache_ttl_hours=1)
    client.request = dummy_request

    # Exact matching for rarity "Rare"
    filter_rare = ItemsFilter(rarity="Rare")
    result_rare = await client.items.query(filter_rare)
    assert len(result_rare) == 1
    assert result_rare[0].id == 3

    # Fuzzy matching for name "wedding"
    filter_fuzzy = ItemsFilter(name=Fuzzy("wedding", cutoff=70))
    result_fuzzy = await client.items.query(filter_fuzzy)
    assert len(result_fuzzy) == 1
    assert result_fuzzy[0].name == "Wedding Gift"

    # Numeric range filtering for marketValue (between 20000 and 10000000)
    filter_market = ItemsFilter(marketValue=(20000, 10000000))
    result_market = await client.items.query(filter_market)
    # Expected: Items with id 1, 2 and 3
    assert len(result_market) == 3

    await client.session.close()
