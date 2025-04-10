import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from rapidfuzz import fuzz

from dankmemer.types import (
    BooleanType,
    DictType,
    IntegerType,
    NumericFilterType,
    StringFilterType,
)
from dankmemer.utils import IN, Above, Below, Fuzzy, Range

if TYPE_CHECKING:
    from dankmemer.client import DankMemerClient


@dataclass(frozen=True)
class Item:
    """
    Represents an individual item obtained from the DankAlert API.

    This immutable class encapsulates all relevant attributes that describe an item,
    such as its identifier, name, details, and various numeric properties. It is designed
    to allow users to interact with item data in a Pythonic way.

    Attributes:
        id (int): The unique identifier of the item.
        name (str): The name of the item.
        details (str): Additional details or description of the item.
        emoji (str): An emoji representation associated with the item.
        flavor (str): A short flavor text providing context or description for the item.
        hasUse (bool): Indicates whether the item has a usable function.
        imageURL (str): The URL pointing to the item's image.
        itemKey (str): A unique string key for the item (e.g. "trash").
        marketValue (int): The market value of the item.
        netValue (int): The net value of the item.
        rarity (str): The rarity classification of the item (e.g. "Common", "Rare").
        skins (Dict[str, Any]): A dictionary of available skins for the item.
        tags (Dict[str, Any]): A dictionary of tags associated with the item.
        type (str): The type or category of the item (e.g. "Sellable", "Loot Box").
        value (int): The intrinsic value or base price of the item.
    """

    id: int
    name: str
    details: str
    emoji: str
    flavor: str
    hasUse: bool
    imageURL: str
    itemKey: str
    marketValue: int
    netValue: int
    rarity: str
    skins: Dict[str, Any]
    tags: Dict[str, Any]
    type: str
    value: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Item":
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            details=data.get("details"),
            emoji=data.get("emoji"),
            flavor=data.get("flavor"),
            hasUse=data.get("hasUse"),
            imageURL=data.get("imageURL"),
            itemKey=data.get("itemKey"),
            marketValue=data.get("marketValue"),
            netValue=data.get("netValue"),
            rarity=data.get("rarity"),
            skins=data.get("skins", {}),
            tags=data.get("tags", {}),
            type=data.get("type"),
            value=data.get("value"),
        )


class ItemsFilter:
    """
    Filter for /items data.
    For string fields, supply a raw string for an exact match or wrap the string in Fuzzy
    for fuzzy matching. Numeric fields accept a single number for exact matching or a tuple
    (min, max) for range filtering.

    Supported filterable attributes:
      - id: Filter by item ID.
      - name: Filter by item name.
      - details: Filter by details.
      - emoji: Filter by emoji.
      - flavor: Filter by flavor.
      - hasUse: Filter by use flag.
      - imageURL: Filter by image URL.
      - itemKey: Filter by item key.
      - marketValue: Filter by market value.
      - netValue: Filter by net value.
      - rarity: Filter by rarity.
      - skins: Filter by skins (exact match).
      - tags: Filter by tags (exact match).
      - type: Filter by type.
      - value: Filter by value.
      - limit: Maximum number of results returned.


    Examples:
        .. code-block:: python

            from dankmemer import Fuzzy, ItemsFilter
            from dankmemer.types import IN, Above, Below, Range


            # Exact string matching for the 'name' field.
            filter_exact = ItemsFilter(name="Trash")

            # Fuzzy matching example for the 'name' field:
            filter_fuzzy = ItemsFilter(name=Fuzzy("trash", cutoff=80))

            # Using IN for membership matching.
            filter_in = ItemsFilter(name=IN("melmsie"))


            # Numeric filtering: filtering 'netValue' for an exact match.
            filter_numeric = ItemsFilter(netValue=100)

            # Numeric filtering with a tuple.
            filter_range = ItemsFilter(marketValue=(5000, 10000000))

            # Numeric filtering with interfaces.
            filter_numeric = ItemsFilter(netValue=Above(10000))
            filter_numeric2 = ItemsFilter(netValue=Below(100000))
            filter_numeric3 = ItemsFilter(netValue=Range(100, 100000))


            # Boolean filtering.
            filter_bool = ItemsFilter(hasUse=True)


    """

    def __init__(
        self,
        id: IntegerType = None,
        name: StringFilterType = None,
        details: StringFilterType = None,
        emoji: StringFilterType = None,
        flavor: StringFilterType = None,
        hasUse: BooleanType = None,
        imageURL: StringFilterType = None,
        itemKey: StringFilterType = None,
        marketValue: NumericFilterType = None,
        netValue: NumericFilterType = None,
        rarity: StringFilterType = None,
        skins: DictType = None,
        tags: DictType = None,
        type: StringFilterType = None,
        value: NumericFilterType = None,
        limit: IntegerType = None,
    ) -> None:
        self.id: IntegerType = id
        self.name: StringFilterType = name
        self.details: StringFilterType = details
        self.emoji: StringFilterType = emoji
        self.flavor: StringFilterType = flavor
        self.hasUse: BooleanType = hasUse
        self.imageURL: StringFilterType = imageURL
        self.itemKey: StringFilterType = itemKey
        self.marketValue: NumericFilterType = marketValue
        self.netValue: NumericFilterType = netValue
        self.rarity: StringFilterType = rarity
        self.skins: DictType = skins
        self.tags: DictType = tags
        self.type: StringFilterType = type
        self.value: NumericFilterType = value
        self.limit: IntegerType = limit

    def apply(self, data: List[Item]) -> List[Item]:
        results: List[Item] = []
        for item in data:
            if self.id is not None and item.id != self.id:
                continue
            if self.name is not None and not self._matches_field(item.name, self.name):
                continue
            if self.details is not None and not self._matches_field(
                item.details, self.details
            ):
                continue
            if self.emoji is not None and not self._matches_field(
                item.emoji, self.emoji
            ):
                continue
            if self.flavor is not None and not self._matches_field(
                item.flavor, self.flavor
            ):
                continue
            if self.hasUse is not None and item.hasUse != self.hasUse:
                continue
            if self.imageURL is not None and not self._matches_field(
                item.imageURL, self.imageURL
            ):
                continue
            if self.itemKey is not None and not self._matches_field(
                item.itemKey, self.itemKey
            ):
                continue
            if self.marketValue is not None and not self._matches_numeric(
                item.marketValue, self.marketValue
            ):
                continue
            if self.netValue is not None and not self._matches_numeric(
                item.netValue, self.netValue
            ):
                continue
            if self.rarity is not None and not self._matches_field(
                item.rarity, self.rarity
            ):
                continue
            if self.skins is not None and item.skins != self.skins:
                continue
            if self.tags is not None and item.tags != self.tags:
                continue
            if self.type is not None and not self._matches_field(item.type, self.type):
                continue
            if self.value is not None and not self._matches_numeric(
                item.value, self.value
            ):
                continue
            results.append(item)
        if self.limit is not None:
            results = results[: self.limit]
        return results

    def _matches_field(self, field_value: str, filter_val: StringFilterType) -> bool:
        if not field_value:
            return False
        if isinstance(filter_val, Fuzzy):
            score: float = fuzz.ratio(field_value.lower(), filter_val.value.lower())
            return score >= filter_val.cutoff
        elif isinstance(filter_val, IN):
            return any(v.lower() in field_value.lower() for v in filter_val.patterns)
        return field_value.lower() == filter_val.lower()  # type: ignore

    def _matches_numeric(
        self, field_value: Union[int, float], filter_val: NumericFilterType
    ) -> bool:
        if isinstance(filter_val, tuple):
            low, high = filter_val
            return low <= field_value <= high
        elif isinstance(filter_val, Above):
            return field_value > filter_val.threshold
        elif isinstance(filter_val, Below):
            return field_value < filter_val.threshold
        elif isinstance(filter_val, Range):
            return filter_val.low <= field_value <= filter_val.high
        return field_value == filter_val


class ItemsRoute:
    """
    Represents the /items endpoint, converting raw API data into python objects and
    providing route-specific filtering.
    """

    def __init__(self, client: "DankMemerClient", cache_ttl: timedelta) -> None:
        self.client: "DankMemerClient" = client
        self.cache_ttl: timedelta = cache_ttl
        self._cache: Optional[Dict[int, Item]] = None
        self._last_update: Optional[datetime] = None
        self._lock: asyncio.Lock = asyncio.Lock()

    async def _fetch(self) -> Dict[int, Item]:
        raw_data: Dict[str, Any] = await self.client.request("items")
        processed: Dict[int, Item] = {}
        for key, value in raw_data.items():
            try:
                item_id: int = int(key)
            except ValueError:
                continue
            processed[item_id] = Item.from_dict(value)
        self._cache = processed
        self._last_update = datetime.now(timezone.utc)
        return processed

    async def _get_data(self) -> Dict[int, Item]:
        async with self._lock:
            if (self._cache is None) or (
                datetime.now(timezone.utc) - self._last_update > self.cache_ttl
            ):
                return await self._fetch()
            return self._cache

    async def query(self, item_filter: Optional[ItemsFilter] = None) -> List[Item]:
        """
        Retrieve the list of Items from the /items endpoint.

        If no filter is provided, all cached items are returned. Otherwise, the provided
        ItemsFilter is applied and only items matching the filter criteria are returned.

        :param item_filter: Optional ItemsFilter instance containing filtering criteria.
        :return: A list of Item objects.
        """
        raw_dict: Dict[int, Item] = await self._get_data()
        items_list: List[Item] = list(raw_dict.values())
        if item_filter is None:
            return items_list
        return item_filter.apply(items_list)
