import pytest
from dankmemer import DankMemerClient, ItemsFilter

@pytest.mark.asyncio
async def test_items_query_without_context_manager():
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
            "value": 100
        },
        "2": {
            "id": 2,
            "name": "Worm",
            "details": "A crawling worm",
            "emoji": "<:Worm:864261394920898600>",
            "flavor": "A small worm",
            "hasUse": True,
            "imageURL": "http://example.com/worm.png",
            "itemKey": "worm",
            "marketValue": 2000,
            "netValue": 200,
            "rarity": "Common",
            "skins": {},
            "tags": {},
            "type": "Sellable",
            "value": 200
        }
    }
    
    async def dummy_request(route: str, params: dict = None):
        return sample_data

    client = DankMemerClient(cache_ttl_hours=1)
    client.request = dummy_request

    # Test boolean filtering: exactly match items with hasUse=True (only "Worm")
    filter_obj = ItemsFilter(hasUse=True)
    result = await client.items.query(filter_obj)
    assert len(result) == 1
    assert result[0].name == "Worm"
    
    await client.session.close()
