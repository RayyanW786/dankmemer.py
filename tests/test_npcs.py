import pytest

from dankmemer import IN, Fuzzy, NPCsFilter, Above
from dankmemer.routes import NPCsRoute
from datetime import timedelta

cache_ttl = timedelta(hours=0)

# Dummy NPC data simulating the API response for /npcs.
dummy_npc_data = {
    "1": {
        "id": "1",
        "name": "Chad",
        "imageURL": "http://example.com/chad.png",
        "extra": {
            "bio": "Friendly and outgoing",
            "nickname": "Chadster",
            "reputation": 50,
            "locations": ["Office", "Cafe"],
        },
    },
    "2": {
        "id": "2",
        "name": "Brad",
        "imageURL": "http://example.com/brad.png",
        "extra": {
            "bio": "Cool and calm",
            "nickname": "Bradley",
            "reputation": 40,
            "locations": ["Gym"],
        },
    },
    "3": {
        "id": "3",
        "name": "NotChad",
        "imageURL": "http://example.com/notchad.png",
        "extra": {
            "bio": "Reserved",
            "nickname": "NotChad",
            "reputation": 10,
            "locations": [],
        },
    },
}


# Create a simple dummy client that only implements the "request" method.
class DummyClient:
    async def request(self, route: str, params: dict = None):
        if route == "npcs":
            return dummy_npc_data
        return {}
    

@pytest.mark.asyncio
async def test_npcs_exact_match():
    """Test exact string filtering on NPC name."""
    client = DummyClient()
    route = NPCsRoute(client, cache_ttl=cache_ttl)
    filter_obj = NPCsFilter(name="Chad")
    npcs = await route.query(filter_obj)
    assert len(npcs) == 1
    assert npcs[0].name == "Chad"


@pytest.mark.asyncio
async def test_npcs_fuzzy_match():
    """Test fuzzy matching on NPC name."""
    client = DummyClient()
    route = NPCsRoute(client, cache_ttl=cache_ttl)
    filter_obj = NPCsFilter(name=Fuzzy("chad", cutoff=70))
    npcs = await route.query(filter_obj)
    names = [npc.name for npc in npcs]
    # Expecting at least "Chad" to match fuzzy criteria.
    assert "Chad" in names
    assert len(npcs) >= 1


@pytest.mark.asyncio
async def test_npcs_in_filter():
    """Test membership filtering (IN) on NPC name."""
    client = DummyClient()
    route = NPCsRoute(client, cache_ttl=cache_ttl)
    filter_obj = NPCsFilter(name=IN("otChad", "Brad"))
    npcs = await route.query(filter_obj)
    names = [npc.name for npc in npcs]
    # Should return both "NotChad" and "Brad".
    assert "NotChad" in names
    assert "Brad" in names
    assert len(npcs) == 2


@pytest.mark.asyncio
async def test_npcs_numeric_filter():
    """Test numeric filtering on NPC reputation."""
    client = DummyClient()
    route = NPCsRoute(client, cache_ttl=cache_ttl)
    # Using a tuple to filter reputation between 30 and 60 should return both Chad and Brad.
    filter_obj = NPCsFilter(reputation=(30, 60))
    npcs = await route.query(filter_obj)
    names = [npc.name for npc in npcs]
    assert "Chad" in names
    assert "Brad" in names

    # Using Above filter for reputation > 45 should return only Chad.
    filter_obj2 = NPCsFilter(reputation=Above(45))
    npcs2 = await route.query(filter_obj2)
    names2 = [npc.name for npc in npcs2]
    assert "Chad" in names2
    assert "Brad" not in names2
