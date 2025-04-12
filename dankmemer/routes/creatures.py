import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from datetime import time as dt_time
from typing import TYPE_CHECKING, Any, AsyncIterator, Dict, List, Optional, Tuple

from rapidfuzz import fuzz

from dankmemer.types import (
    BooleanType,
    IntegerType,
    StringFilterType,
    StringType,
)
from dankmemer.utils import IN, DotDict, Fuzzy

if TYPE_CHECKING:
    from dankmemer.client import DankMemerClient


def parse_time_info(time_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse the time information from a creature's extra data.
    
    Converts the 'start' and 'end' numeric values (assumed to represent hours in 24-hour format)
    into datetime.time objects. If a 'reversed' key is present and True, the start and end values
    are swapped before conversion. If start is 0 and end is 24, the creature is available all day,
    so a flag 'full_day': True is added and both times are normalized to 00:00.
    Additionally, any occurrence of 24 (which is invalid) is converted to 0.
    
    :param time_info: A dictionary with keys "start", "end" and optionally "reversed".
    :return: The updated time_info dictionary with "start" and "end" as dt_time objects.
    """
    reversed_val = time_info.get("reversed", False)
    start_hour = time_info.get("start")
    end_hour = time_info.get("end")
    
    if start_hour is not None and end_hour is not None:
        # Check for full-day availability.
        if start_hour == 0 and end_hour == 24:
            time_info["full_day"] = True
            time_info["start"] = dt_time(hour=0)
            time_info["end"] = dt_time(hour=0)
        else:
            if reversed_val:
                start_hour, end_hour = end_hour, start_hour
            # Convert any occurrence of 24 to 0.
            if start_hour == 24:
                start_hour = 0
            if end_hour == 24:
                end_hour = 0
            try:
                time_info["start"] = dt_time(hour=int(start_hour))
                time_info["end"] = dt_time(hour=int(end_hour))
            except Exception:
                # If conversion fails, leave original values.
                pass
    return time_info


@dataclass(frozen=True)
class Creature:
    """
    Represents an individual creature obtained from the DankAlert API.

    Attributes:
        id (str): The unique identifier of the creature.
        name (str): The name of the creature.
        imageURL (str): The URL for the creature's image.
        extra (Dict[str, Any]): A dictionary of additional creature data. Typically includes:
          - boss (bool): Whether the creature is a boss.
          - flavor (str): A short flavor text description.
          - locations (List[str]): A list of locations where the creature can be found.
          - mythical (bool): Whether the creature is mythical.
          - rarity (str): The rarity classification of the creature.
          - time (dict): Time range information for availability.
          - variants (List[dict]): Optional list of variant information.
    """

    id: str
    name: str
    imageURL: str
    extra: DotDict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Creature":
        extra_data = data.get("extra", {})
        if not isinstance(extra_data, DotDict):
            extra_data = DotDict(extra_data)
        if "time" in extra_data:
            extra_data["time"] = parse_time_info(extra_data["time"])
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            imageURL=data.get("imageURL"),
            extra=extra_data,
        )

    def __getattr__(self, attribute: str) -> Any:
        """
        Fallback attribute lookup: if an attribute is not found normally,
        attempt to retrieve it from the extra data.
        """
        if attribute in self.extra:
            return self.extra[attribute]
        raise AttributeError(f"'Creature' object has no attribute '{attribute}'")

    def get_availability_window(self) -> Tuple[datetime, datetime]:
        """
        Returns a tuple (start_dt, end_dt) representing the creature's spawn availability window
        for the current UTC day.
        
        Uses the creature's extra["time"] field (which must contain 'start' and 'end' as dt_time objects).
        
        If the "full_day" flag is set, returns a window from today's 00:00 UTC until tomorrow's 00:00 UTC.
        Otherwise, if the start datetime is later than the end datetime (indicating the window spans midnight),
        end_dt is adjusted to the next day.
        
        :return: A tuple of datetime objects (spawn_start, spawn_end).
        :raises ValueError: If the time fields are missing or invalid.
        """
        time_data = self.extra.get("time", {})
        start_val = time_data.get("start")
        end_val = time_data.get("end")
        if not isinstance(start_val, dt_time) or not isinstance(end_val, dt_time):
            raise ValueError("Creature has invalid or missing 'start'/'end' time fields.")
        
        current_utc_date = datetime.now(timezone.utc).date()
        start_dt = datetime.combine(current_utc_date, start_val, tzinfo=timezone.utc)
        # If full day, end is tomorrow at 00:00 UTC.
        if time_data.get("full_day", False):
            end_dt = datetime.combine(current_utc_date + timedelta(days=1), dt_time(hour=0), tzinfo=timezone.utc)
        else:
            end_dt = datetime.combine(current_utc_date, end_val, tzinfo=timezone.utc)
            if start_dt > end_dt:
                end_dt += timedelta(days=1)
        return start_dt, end_dt


class CreaturesFilter:
    """
    Filter for /creatures data.

    You can filter on:
      - id: (str) exact match.
      - name: (StringFilterType) string matching (exact, fuzzy using Fuzzy, or membership using IN).
      - imageURL: (StringFilterType) match on the creature's image URL.
      - flavor: (StringFilterType) applied to extra.flavor.
      - boss: (BooleanType) filter on extra.boss.
      - mythical: (BooleanType) filter on extra.mythical.
      - rarity: (StringFilterType) filter on extra.rarity.
      - locations: (StringFilterType) matches if any location in extra.locations matches.
      - limit: (int) maximum number of results returned.

    Examples:
        .. code-block:: python

            from dankmemer import CreaturesFilter, Fuzzy, IN, Above, Below, Range

            # Exact matching on the 'name' field.
            filter_exact = CreaturesFilter(name="Ahuitzotl")

            # Fuzzy matching on the 'name' field.
            filter_fuzzy = CreaturesFilter(name=Fuzzy("ahuitzotl", cutoff=75))

            # Membership matching using IN.
            filter_in = CreaturesFilter(name=IN("blood", "hoop"))

            # Boolean filtering: filtering by boss status.
            filter_boss = CreaturesFilter(boss=True)

            # Filtering by rarity.
            filter_rarity = CreaturesFilter(rarity="Absurdly Rare")

            # Filtering by locations.
            filter_locations = CreaturesFilter(locations=IN("lake"))
    """

    def __init__(
        self,
        id: StringType = None,
        name: StringFilterType = None,
        imageURL: StringFilterType = None,
        flavor: StringFilterType = None,
        boss: BooleanType = None,
        mythical: BooleanType = None,
        rarity: StringFilterType = None,
        locations: StringFilterType = None,
        limit: IntegerType = None,
    ) -> None:
        self.id: StringType = id
        self.name: StringFilterType = name
        self.imageURL: StringFilterType = imageURL
        self.flavor: StringFilterType = flavor
        self.boss: BooleanType = boss
        self.mythical: BooleanType = mythical
        self.rarity: StringFilterType = rarity
        self.locations: StringFilterType = locations
        self.limit: IntegerType = limit

    def apply(self, data: List[Creature]) -> List[Creature]:
        results: List[Creature] = []
        for creature in data:
            if self.id is not None and creature.id != self.id:
                continue
            if self.name is not None and not self._matches_field(
                creature.name, self.name
            ):
                continue
            if self.imageURL is not None and not self._matches_field(
                creature.imageURL, self.imageURL
            ):
                continue
            extra = creature.extra
            if self.flavor is not None:
                flav = extra.get("flavor", "")
                if not self._matches_field(flav, self.flavor):
                    continue
            if self.boss is not None:
                boss_val = extra.get("boss")
                if boss_val != self.boss:
                    continue
            if self.mythical is not None:
                mythical_val = extra.get("mythical")
                if mythical_val != self.mythical:
                    continue
            if self.rarity is not None:
                rarity_val = extra.get("rarity", "")
                if not self._matches_field(rarity_val, self.rarity):
                    continue
            if self.locations is not None:
                locs = extra.get("locations", [])
                if not self._matches_list(locs, self.locations):
                    continue
            results.append(creature)
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
            return any(p.lower() in field_value.lower() for p in filter_val.patterns)
        return field_value.lower() == filter_val.lower()

    def _matches_list(
        self, field_list: List[Any], filter_val: StringFilterType
    ) -> bool:
        for element in field_list:
            if isinstance(element, str) and self._matches_field(element, filter_val):
                return True
            if element == filter_val:
                return True
        return False


class CreaturesRoute:
    """
    Represents the /creatures endpoint, converting raw API data into Creature objects
    and providing route-specific filtering.
    """

    def __init__(self, client: "DankMemerClient", cache_ttl: timedelta) -> None:
        self.client: "DankMemerClient" = client
        self.cache_ttl: timedelta = cache_ttl
        self._cache: Optional[Dict[str, Creature]] = None
        self._last_update: Optional[datetime] = None
        self._lock: asyncio.Lock = asyncio.Lock()

    async def _fetch(self) -> Dict[str, Creature]:
        raw_data: Dict[str, Any] = await self.client.request("creatures")
        processed: Dict[str, Creature] = {}
        for key, value in raw_data.items():
            processed[key] = Creature.from_dict(value)
        self._cache = processed
        self._last_update = datetime.now(timezone.utc)
        return processed

    async def _get_data(self) -> Dict[str, Creature]:
        async with self._lock:
            if (self._cache is None) or (
                datetime.now(timezone.utc) - self._last_update > self.cache_ttl
            ):
                return await self._fetch()
            return self._cache

    async def query(
        self, creature_filter: Optional[CreaturesFilter] = None
    ) -> List[Creature]:
        """
        Retrieve the list of Creature objects from the /creatures endpoint.

        If a CreaturesFilter is provided, only creatures matching the filtering criteria are returned.

        :param creature_filter: Optional CreaturesFilter instance containing filtering criteria.
        :return: A list of Creature objects.
        """
        raw_dict: Dict[str, Creature] = await self._get_data()
        creatures_list: List[Creature] = list(raw_dict.values())
        if creature_filter is not None:
            creatures_list = creature_filter.apply(creatures_list)
        return creatures_list

    async def iter_query(
        self, creature_filter: Optional[CreaturesFilter] = None
    ) -> AsyncIterator[Creature]:
        """
        Asynchronously iterates over Creature objects from the /creatures endpoint.

        If a CreaturesFilter is provided, only creatures matching the filter criteria are yielded.

        Yields:
            Each Creature object from the query results.
        """
        raw_dict: Dict[str, Creature] = await self._get_data()
        creatures_list: List[Creature] = list(raw_dict.values())
        if creature_filter is not None:
            creatures_list = creature_filter.apply(creatures_list)
        for creature in creatures_list:
            yield creature
