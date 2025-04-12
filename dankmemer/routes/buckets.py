import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, AsyncIterator, Dict, List, Optional, Union

from dankmemer.types import (
    IntegerType,
    NumericFilterType,
    StringFilterType,
    StringType,
)
from dankmemer.utils import IN, Above, Below, DotDict, Fuzzy, Range

if TYPE_CHECKING:
    from dankmemer.client import DankMemerClient


@dataclass(frozen=True)
class Bucket:
    """
    Represents a bucket obtained from the DankAlert API.

    Attributes:
        id (str): The unique identifier for the bucket.
        name (str): The name of the bucket.
        imageURL (str): The URL of the bucket's image.
        extra (Dict[str, Any]): Additional bucket data.
            - flavor (str): A descriptive flavor text.
            - size (int): The size of the bucket.
    """

    id: str
    name: str
    imageURL: str
    extra: DotDict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Bucket":
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
        Fallback attribute lookup: if an attribute is not found normally,
        attempt to retrieve it from the extra data.
        """
        if attribute in self.extra:
            return self.extra[attribute]
        raise AttributeError(f"'Bucket' object has no attribute '{attribute}'")


class BucketsFilter:
    """
    Filter for /buckets data.

    You can filter on:
      - id: (str) exact match.
      - name: (StringFilterType) string matching (exact, fuzzy via Fuzzy, or membership using IN).
      - imageURL: (StringFilterType) match on the bucket's image URL.
      - flavor: (StringFilterType) filtering applied to extra.flavor.
      - size: (NumericFilterType) numeric filtering on extra.size (supports exact value, tuple range, or interfaces Above, Below, Range).
      - limit: (int) maximum number of results returned.

    Examples:
        .. code-block:: python

            from dankmemer import BucketsFilter, Fuzzy, IN, Above, Below, Range

            # Exact string matching for the 'name' field.
            filter_exact = BucketsFilter(name="Golden Bucket")

            # Fuzzy matching for the 'name' field.
            filter_fuzzy = BucketsFilter(name=Fuzzy("golden", cutoff=80))

            # Membership matching using IN for the 'name' field.
            filter_in = BucketsFilter(name=IN("bucket"))

            # Numeric filtering: filtering 'size' for an exact match.
            filter_numeric = BucketsFilter(size=50)

            # Numeric filtering with a tuple range.
            filter_range = BucketsFilter(size=(10, 50))

            # Numeric filtering using interfaces.
            filter_above = BucketsFilter(size=Above(20))
            filter_below = BucketsFilter(size=Below(60))
            filter_range_interface = BucketsFilter(size=Range(25, 75))
    """

    def __init__(
        self,
        id: StringType = None,
        name: StringFilterType = None,
        imageURL: StringFilterType = None,
        flavor: StringFilterType = None,
        size: NumericFilterType = None,
        limit: IntegerType = None,
    ) -> None:
        self.id: StringType = id
        self.name: StringFilterType = name
        self.imageURL: StringFilterType = imageURL
        self.flavor: StringFilterType = flavor
        self.size: NumericFilterType = size
        self.limit: IntegerType = limit

    def apply(self, data: List[Bucket]) -> List[Bucket]:
        results: List[Bucket] = []
        for bucket in data:
            if self.id is not None and bucket.id != self.id:
                continue
            if self.name is not None and not self._matches_field(
                bucket.name, self.name
            ):
                continue
            if self.imageURL is not None and not self._matches_field(
                bucket.imageURL, self.imageURL
            ):
                continue

            extra = bucket.extra
            if self.flavor is not None:
                flavor_val = extra.get("flavor", "")
                if not self._matches_field(flavor_val, self.flavor):
                    continue
            if self.size is not None:
                s = extra.get("size")
                if s is None or not self._matches_numeric(s, self.size):
                    continue
            results.append(bucket)
        if self.limit is not None:
            results = results[: self.limit]
        return results

    def _matches_field(self, field_value: str, filter_val: StringFilterType) -> bool:
        if not field_value:
            return False
        if isinstance(filter_val, Fuzzy):
            from rapidfuzz import fuzz

            score: float = fuzz.ratio(field_value.lower(), filter_val.value.lower())
            return score >= filter_val.cutoff
        elif isinstance(filter_val, IN):
            return any(p.lower() in field_value.lower() for p in filter_val.patterns)
        else:
            return field_value.lower() == filter_val.lower()

    def _matches_numeric(
        self, field_value: Union[int, float], filter_val: NumericFilterType
    ) -> bool:
        try:
            value = float(field_value)
        except (ValueError, TypeError):
            return False

        if isinstance(filter_val, tuple):
            low, high = filter_val
            return low <= value <= high
        elif isinstance(filter_val, Above):
            return value > filter_val.threshold
        elif isinstance(filter_val, Below):
            return value < filter_val.threshold
        elif isinstance(filter_val, Range):
            return filter_val.low <= value <= filter_val.high
        else:
            try:
                return value == float(filter_val)
            except (ValueError, TypeError):
                return False


class BucketsRoute:
    """
    Represents the /buckets endpoint, converting raw API data into Bucket objects and
    providing route-specific filtering.
    """

    def __init__(self, client: "DankMemerClient", cache_ttl: timedelta) -> None:
        self.client: "DankMemerClient" = client
        self.cache_ttl: timedelta = cache_ttl
        self._cache: Optional[Dict[str, Bucket]] = None
        self._last_update: Optional[datetime] = None
        self._lock: asyncio.Lock = asyncio.Lock()

    async def _fetch(self) -> Dict[str, Bucket]:
        raw_data: Dict[str, Any] = await self.client.request("buckets")
        processed: Dict[str, Bucket] = {}
        for key, value in raw_data.items():
            processed[key] = Bucket.from_dict(value)
        self._cache = processed
        self._last_update = datetime.now(timezone.utc)
        return processed

    async def _get_data(self) -> Dict[str, Bucket]:
        async with self._lock:
            if (self._cache is None) or (
                datetime.now(timezone.utc) - self._last_update > self.cache_ttl
            ):
                return await self._fetch()
            return self._cache

    async def query(
        self, bucket_filter: Optional[BucketsFilter] = None
    ) -> List[Bucket]:
        """
        Retrieve the list of Bucket objects from the /buckets endpoint.

        If a BucketsFilter is provided, only buckets matching the criteria are returned.

        :param bucket_filter: Optional BucketsFilter instance for filtering criteria.
        :return: A list of Bucket objects.
        """
        raw_dict: Dict[str, Bucket] = await self._get_data()
        buckets_list: List[Bucket] = list(raw_dict.values())
        if bucket_filter is not None:
            buckets_list = bucket_filter.apply(buckets_list)
        return buckets_list

    async def iter_query(
        self, bucket_filter: Optional[BucketsFilter] = None
    ) -> AsyncIterator[Bucket]:
        """
        Asynchronously iterate over Bucket objects from the /buckets endpoint.

        :param bucket_filter: Optional BucketsFilter instance for filtering.
        :yield: Each Bucket object that matches the filter.
        """
        raw_dict: Dict[str, Bucket] = await self._get_data()
        buckets_list: List[Bucket] = list(raw_dict.values())
        if bucket_filter is not None:
            buckets_list = bucket_filter.apply(buckets_list)
        for bucket in buckets_list:
            yield bucket
