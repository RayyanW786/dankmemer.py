import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, AsyncIterator, Dict, List, Optional

from rapidfuzz import fuzz

from dankmemer.types import StringFilterType, StringType, BooleanType, IntegerType
from dankmemer.utils import DotDict, Fuzzy, IN

if TYPE_CHECKING:
    from dankmemer.client import DankMemerClient


@dataclass(frozen=True)
class Season:
    """
    Represents a season event (or season pass) from the DankAlert API.

    Attributes:
        id (str): The unique identifier of the season.
        name (str): The display name of the season.
        imageURL (str): The URL pointing to the season's image.
        extra (DotDict): A dictionary of additional season data. This typically includes:
            - active (bool): Whether the season event is currently active.
            - freeRewards (List[Dict[str, Any]]): List of free rewards.
            - premiumRewards (List[Dict[str, Any]]): List of premium rewards.
    """
    id: str
    name: str
    imageURL: str
    extra: DotDict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Season":
        extra_data = data.get("extra", {})
        if not isinstance(extra_data, DotDict):
            extra_data = DotDict(extra_data)
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            imageURL=data.get("imageURL"),
            extra=extra_data,
        )

    def __getattr__(self, attribute: str) -> Any:
        """
        Fallback attribute lookup. Allows direct access to fields in the extra dictionary.
        
        :param attribute: The attribute name.
        :return: The value stored in self.extra if present.
        :raises AttributeError: If the attribute is not found.
        """
        if attribute in self.extra:
            return self.extra[attribute]
        raise AttributeError(f"'Season' object has no attribute '{attribute}'")


class SeasonsFilter:
    """
    Filter for /seasons data.

    You can filter on:
      - id: (str) Exact match on season id.
      - name: (StringFilterType) String matching on the season name (supports exact matching,
              fuzzy matching using Fuzzy, or membership matching using IN).
      - active: (BooleanType) Filter based on the season's active status.
      - limit: (int) Maximum number of results to return.

    Examples:
        .. code-block:: python

            from dankmemer import SeasonsFilter, Fuzzy, IN

            # Exact matching on the 'name' field.
            filter_exact = SeasonsFilter(name="season-1-pass")

            # Fuzzy matching on the 'name' field.
            filter_fuzzy = SeasonsFilter(name=Fuzzy("pass", cutoff=70))

            # Filtering based on active status.
            filter_active = SeasonsFilter(active=True)
    """
    def __init__(
        self,
        id: StringType = None,
        name: StringFilterType = None,
        active: BooleanType = None,
        limit: IntegerType = None,
    ) -> None:
        self.id: StringType = id
        self.name: StringFilterType = name
        self.active: BooleanType = active
        self.limit: IntegerType = limit

    def apply(self, data: List[Season]) -> List[Season]:
        results: List[Season] = []
        for season in data:
            if self.id is not None and season.id != self.id:
                continue
            if self.name is not None and not self._matches_field(season.name, self.name):
                continue
            if self.active is not None:
                if season.extra.get("active", False) != self.active:
                    continue
            results.append(season)
        if self.limit is not None:
            results = results[: self.limit]
        return results

    def _matches_field(self, field_value: str, filter_val: StringFilterType) -> bool:
        if not field_value:
            return False
        if isinstance(filter_val, Fuzzy):
            return fuzz.ratio(field_value.lower(), filter_val.value.lower()) >= filter_val.cutoff
        elif isinstance(filter_val, IN):
            return any(p.lower() in field_value.lower() for p in filter_val.patterns)
        else:
            return field_value.lower() == filter_val.lower()


class SeasonsRoute:
    """
    Represents the /seasons endpoint, converting raw API data into Season objects and
    providing route-specific filtering.
    """

    def __init__(self, client: "DankMemerClient", cache_ttl: timedelta) -> None:
        self.client = client
        self.cache_ttl = cache_ttl
        self._cache: Optional[Dict[str, Season]] = None
        self._last_update: Optional[datetime] = None
        self._lock = asyncio.Lock()

    async def _fetch(self) -> Dict[str, Season]:
        raw_data: Dict[str, Any] = await self.client.request("seasons")
        processed: Dict[str, Season] = {}
        for key, value in raw_data.items():
            processed[key] = Season.from_dict(value)
        self._cache = processed
        self._last_update = datetime.now(timezone.utc)
        return processed

    async def _get_data(self) -> Dict[str, Season]:
        async with self._lock:
            if self._cache is None or datetime.now(timezone.utc) - self._last_update > self.cache_ttl:
                return await self._fetch()
            return self._cache

    async def query(self, season_filter: Optional[SeasonsFilter] = None) -> List[Season]:
        """
        Retrieve the list of Season objects from the /seasons endpoint.

        If a SeasonsFilter is provided, the returned list is filtered accordingly.

        :param season_filter: Optional SeasonsFilter instance containing filtering criteria.
        :return: A list of Season objects.
        """
        raw_dict = await self._get_data()
        seasons_list = list(raw_dict.values())
        if season_filter is not None:
            seasons_list = season_filter.apply(seasons_list)
        return seasons_list

    async def iter_query(self, season_filter: Optional[SeasonsFilter] = None) -> AsyncIterator[Season]:
        """
        Asynchronously iterates over Season objects from the /seasons endpoint.

        :param season_filter: Optional SeasonsFilter instance for filtering.
        :yield: Each Season object that matches the filtering criteria.
        """
        raw_dict = await self._get_data()
        seasons_list = list(raw_dict.values())
        if season_filter is not None:
            seasons_list = season_filter.apply(seasons_list)
        for season in seasons_list:
            yield season
