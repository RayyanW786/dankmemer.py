import asyncio
import time
from datetime import timedelta
from typing import Optional

import aiohttp

from dankmemer.routes import items


class DankMemerClient:
    """
    An asynchronous client for accessing the DankAlert API.

    This client manages and provides access to various API endpoints
    (e.g. items, npcs, skills, tools) along with built-in caching. In addition, it supports
    anti-rate-limit behavior: when 'useAntirateLimit' is enabled (the default), the client
    ensures that no more than 60 requests are made every 60 seconds.

    Recommended usage:
      As a context manager:
        async with DankMemerClient(cache_ttl_hours=24) as client:
            items = await client.items.query()

      Without a context manager:
        client = DankMemerClient(cache_ttl_hours=24)
        items = await client.items.query()
        await client.session.close()
    """

    def __init__(
        self,
        *,
        useAntirateLimit: bool = True,
        base_url="https://api.dankalert.xyz/dank",
        session: Optional[aiohttp.ClientSession] = None,
        cache_ttl_hours: int = 24,
    ):
        self.use_anti_ratelimit = useAntirateLimit
        self.base_url = base_url.rstrip("/")
        self.session = session or aiohttp.ClientSession()
        if cache_ttl_hours < 1:
            raise ValueError("cache_ttl_hours must be at least 1 hour")
        self.cache_ttl = timedelta(hours=cache_ttl_hours)

        # Rate-limiting (current API: 60 requests per 60 seconds)
        self._rate_limit_lock = asyncio.Lock()
        self.max_requests: int = 60
        self.request_period: float = 60.0
        self._request_times: list[float] = []

        self.items = items.ItemsRoute(self, self.cache_ttl)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.session:
            await self.session.close()

    async def request(self, route: str, params: dict = None):
        """
        Makes an HTTP GET request to the specified route with the given query parameters,
        while enforcing the API's rate limiting if useAntirateLimit is enabled.

        :param route: The API route to request (appended to the base URL).
        :param params: Optional dictionary of query parameters.
        :return: The parsed JSON response.
        """

        # Rate-limiting check:
        # We perform a single check on the _request_times list and sleep if needed.
        # Because all access to _request_times is serialized using an asyncio lock,
        # and our expected usage pattern doesn't involve huge bursts of concurrent requests,
        # a single check is sufficient to enforce the rate limit.
        # If the system were to experience significant bursts, a while loop could be added
        # to continuously re-check the condition after sleeping. However, given our design,
        # the one-time check and sleep approach provides a simpler and maintainable solution.

        if self.use_anti_ratelimit:
            async with self._rate_limit_lock:
                now: float = time.monotonic()
                self._request_times = [
                    t for t in self._request_times if now - t < self.request_period
                ]
                if len(self._request_times) >= self.max_requests:
                    wait_time: float = self.request_period - (
                        now - self._request_times[0]
                    )
                    await asyncio.sleep(wait_time)
                    now = time.monotonic()
                    self._request_times = [
                        t for t in self._request_times if now - t < self.request_period
                    ]
                self._request_times.append(now)

        url = f"{self.base_url}/{route}"
        async with self.session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()
