import asyncio
from datetime import timedelta

import pytest

from dankmemer import DankMemerClient
from dankmemer.routes.baits import BaitsFilter, BaitsRoute
from dankmemer.utils import IN, Above, Below, Fuzzy, Range

# Dummy data simulating the response from api.dankalert.xyz/dank/baits
dummy_baits_data = {
    "deadly-bait": {
        "id": "deadly-bait",
        "name": "Deadly Bait",
        "imageURL": "https://cdn.discordapp.com/emojis/1170466291358900255.gif",
        "extra": {
            "explanation": "This bait increases both the chance to catch a boss (5x) and the chance to catch a boss variant (2x). Consumed when you catch a boss.",
            "flavor": "This was used to catch a monster. Now, the monster uses it.",
            "idle": False,
            "usage": 1,
        },
    },
    "eyeball-bait": {
        "id": "eyeball-bait",
        "name": "Eyeball Bait",
        "imageURL": "https://cdn.discordapp.com/emojis/1143118957075767347.png",
        "extra": {
            "explanation": "Heavily increases the odds of catching a unique variant or chroma fish. Found during Halloween.",
            "flavor": "This bait only has an eye for the really valuable fish. Wait... why is it looking at me like that?",
            "idle": True,
            "usage": 2,
        },
    },
    "gift-bait": {
        "id": "gift-bait",
        "name": "Gift Bait",
        "imageURL": "https://cdn.discordapp.com/emojis/1156866494865604649.png",
        "extra": {
            "explanation": "Adds a chance to get winter items while fishing. Used when a winter item is caught.",
            "flavor": "I certainly hope I got the Naboo Swamp & Gungan Sub Lego set that I asked for.",
            "idle": False,
            "usage": 5,
        },
    },
}


class DummyBaitsClient(DankMemerClient):
    """
    A client subclass that overrides the request method to return dummy data for baits.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.session:
            asyncio.create_task(self.session.close())

    async def request(self, route: str, params: dict = None):
        if route == "baits":
            return dummy_baits_data
        return {}


@pytest.mark.asyncio
async def test_baits_exact_match():
    """
    Test exact string matching on bait name: Should return only 'Gift Bait'.
    """
    client = DummyBaitsClient(cache_ttl_hours=1)
    route = BaitsRoute(client, cache_ttl=timedelta(seconds=0))
    filter_obj = BaitsFilter(name="Gift Bait")
    baits = await route.query(filter_obj)
    names = [bait.name for bait in baits]
    assert names == ["Gift Bait"]


@pytest.mark.asyncio
async def test_baits_fuzzy_match():
    """
    Test fuzzy matching for bait name: 'Eyeball Bait' should match fuzzy search for 'eyeball'.
    """
    client = DummyBaitsClient(cache_ttl_hours=1)
    route = BaitsRoute(client, cache_ttl=timedelta(seconds=0))
    filter_obj = BaitsFilter(name=Fuzzy("eyeball", cutoff=70))
    baits = await route.query(filter_obj)
    names = [bait.name for bait in baits]
    assert "Eyeball Bait" in names


@pytest.mark.asyncio
async def test_baits_in_filter():
    """
    Test membership filtering using the IN interface:
    'deadly-bait' name includes 'Deadly Bait', so using IN('deadly') should match it.
    """
    client = DummyBaitsClient(cache_ttl_hours=1)
    route = BaitsRoute(client, cache_ttl=timedelta(seconds=0))
    filter_obj = BaitsFilter(name=IN("deadly"))
    baits = await route.query(filter_obj)
    names = [bait.name for bait in baits]
    assert "Deadly Bait" in names


@pytest.mark.asyncio
async def test_baits_boolean_filter():
    """
    Test boolean filtering on 'idle'.
    Eyeball Bait has idle == True, so filter_obj with idle=True should return it.
    """
    client = DummyBaitsClient(cache_ttl_hours=1)
    route = BaitsRoute(client, cache_ttl=timedelta(seconds=0))
    filter_obj = BaitsFilter(idle=True)
    baits = await route.query(filter_obj)
    names = [bait.name for bait in baits]
    assert names == ["Eyeball Bait"]


@pytest.mark.asyncio
async def test_baits_numeric_exact():
    """
    Test numeric filtering with an exact match on usage.
    Gift Bait has usage=5, so usage=5 should return only Gift Bait.
    """
    client = DummyBaitsClient(cache_ttl_hours=1)
    route = BaitsRoute(client, cache_ttl=timedelta(seconds=0))
    filter_obj = BaitsFilter(usage=5)
    baits = await route.query(filter_obj)
    names = [bait.name for bait in baits]
    assert names == ["Gift Bait"]


@pytest.mark.asyncio
async def test_baits_numeric_range():
    """
    Test numeric filtering using a tuple.
    usage=(1, 2) should match 'Deadly Bait' (usage=1) and 'Eyeball Bait' (usage=2).
    """
    client = DummyBaitsClient(cache_ttl_hours=1)
    route = BaitsRoute(client, cache_ttl=timedelta(seconds=0))
    filter_obj = BaitsFilter(usage=(1, 2))
    baits = await route.query(filter_obj)
    names = sorted(bait.name for bait in baits)
    assert names == ["Deadly Bait", "Eyeball Bait"]


@pytest.mark.asyncio
async def test_baits_numeric_interfaces():
    """
    Test numeric filtering using Above, Below, and Range.
    """
    client = DummyBaitsClient(cache_ttl_hours=1)
    route = BaitsRoute(client, cache_ttl=timedelta(seconds=0))

    # usage > 1 => Eyeball Bait (2) and Gift Bait (5)
    filter_above = BaitsFilter(usage=Above(1))
    baits_above = await route.query(filter_above)
    names_above = sorted(bait.name for bait in baits_above)
    assert names_above == ["Eyeball Bait", "Gift Bait"]

    # usage < 5 => Deadly Bait (1) and Eyeball Bait (2)
    filter_below = BaitsFilter(usage=Below(5))
    baits_below = await route.query(filter_below)
    names_below = sorted(bait.name for bait in baits_below)
    assert names_below == ["Deadly Bait", "Eyeball Bait"]

    # usage between 2 and 10 => Eyeball Bait (2), Gift Bait (5)
    filter_range = BaitsFilter(usage=Range(2, 10))
    baits_range = await route.query(filter_range)
    names_range = sorted(bait.name for bait in baits_range)
    assert names_range == ["Eyeball Bait", "Gift Bait"]
