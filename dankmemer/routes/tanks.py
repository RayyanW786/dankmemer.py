import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, AsyncIterator, Dict, List, Optional

from rapidfuzz import fuzz

from dankmemer.types import IntegerType, StringFilterType, StringType
from dankmemer.utils import IN, DotDict, Fuzzy

if TYPE_CHECKING:
    from dankmemer.client import DankMemerClient


@dataclass(frozen=True)
class Tank:
    """
    Represents an individual tank (fishtank) entry obtained from the DankAlert API.

    Attributes:
        id (str): The unique identifier for the tank.
        name (str): The name of the tank.
        imageURL (str): The URL of the tank's image.
        extra (DotDict): Additional tank data (currently empty in the sample).
    """
    id: str
    name: str
    imageURL: str
    extra: DotDict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Tank":
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
        Fallback attribute lookup: if an attribute is not found on the Tank instance,
        attempt to retrieve it from the extra data.
        """
        if attribute in self.extra:
            return self.extra[attribute]
        raise AttributeError(f"'Tank' object has no attribute '{attribute}'")


class TanksFilter:
    """
    Filter for /tanks data.

    Supported filterable attributes:
      - id: (str) Exact match.
      - name: (StringFilterType) String matching on the tank's name (exact, fuzzy via Fuzzy, or membership using IN).
      - imageURL: (StringFilterType) Filtering on the tank's image URL.
      - limit: (int) Maximum number of results returned.

    Examples:
        .. code-block:: python
        
            from dankmemer import TanksFilter, Fuzzy, IN
            
            filter_exact = TanksFilter(name="Blue")
            filter_fuzzy = TanksFilter(name=Fuzzy("blue", cutoff=80))
            filter_in = TanksFilter(name=IN("tank"))
    """
    def __init__(
        self,
        id: StringType = None,
        name: StringFilterType = None,
        imageURL: StringFilterType = None,
        limit: IntegerType = None,
    ) -> None:
        self.id: StringType = id
        self.name: StringFilterType = name
        self.imageURL: StringFilterType = imageURL
        self.limit: IntegerType = limit

    def apply(self, data: List[Tank]) -> List[Tank]:
        results: List[Tank] = []
        for tank in data:
            if self.id is not None and tank.id != self.id:
                continue
            if self.name is not None and not self._matches_field(tank.name, self.name):
                continue
            if self.imageURL is not None and not self._matches_field(tank.imageURL, self.imageURL):
                continue
            results.append(tank)
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
            return any(pattern.lower() in field_value.lower() for pattern in filter_val.patterns)
        return field_value.lower() == filter_val.lower()


class TanksRoute:
    """
    Represents the /tanks endpoint, converting raw API data into Tank objects and
    providing route-specific filtering.
    """
    def __init__(self, client: "DankMemerClient", cache_ttl: timedelta) -> None:
        self.client = client
        self.cache_ttl = cache_ttl
        self._cache: Optional[Dict[str, Tank]] = None
        self._last_update: Optional[datetime] = None
        self._lock: asyncio.Lock = asyncio.Lock()

    async def _fetch(self) -> Dict[str, Tank]:
        raw_data: Dict[str, Any] = await self.client.request("tanks")
        processed: Dict[str, Tank] = {}
        for key, value in raw_data.items():
            processed[key] = Tank.from_dict(value)
        self._cache = processed
        self._last_update = datetime.now(timezone.utc)
        return processed

    async def _get_data(self) -> Dict[str, Tank]:
        async with self._lock:
            if self._cache is None or (datetime.now(timezone.utc) - self._last_update > self.cache_ttl):
                return await self._fetch()
            return self._cache

    async def query(self, tank_filter: Optional[TanksFilter] = None) -> List[Tank]:
        """
        Retrieves a list of Tank objects from the /tanks endpoint.
        If a TanksFilter is provided, returns only the tanks matching the filter criteria.

        :param tank_filter: Optional TanksFilter instance containing filtering criteria.
        :return: A list of Tank objects.
        """
        raw_dict: Dict[str, Tank] = await self._get_data()
        tank_list: List[Tank] = list(raw_dict.values())
        if tank_filter is not None:
            tank_list = tank_filter.apply(tank_list)
        return tank_list

    async def iter_query(self, tank_filter: Optional[TanksFilter] = None) -> AsyncIterator[Tank]:
        """
        Asynchronously iterates over Tank objects from the /tanks endpoint.
        If a TanksFilter is provided, only tanks matching the criteria are iterated.

        :param tank_filter: Optional TanksFilter instance for filtering.
        :yield: Tank objects.
        """
        raw_dict: Dict[str, Tank] = await self._get_data()
        tank_list: List[Tank] = list(raw_dict.values())
        if tank_filter is not None:
            tank_list = tank_filter.apply(tank_list)
        for tank in tank_list:
            yield tank
