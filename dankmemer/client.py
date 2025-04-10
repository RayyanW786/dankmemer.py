import asyncio
import logging
import random
import time
from datetime import timedelta
from typing import Optional

import aiohttp

from dankmemer.exceptions import (
    BadRequestException,
    DankMemerHTTPException,
    NotFoundException,
    RateLimitException,
    ServerErrorException,
)
from dankmemer.routes import items, npcs

COLOR_CODES = {
    logging.INFO: "\033[94m",
    logging.WARNING: "\033[93m",
    logging.ERROR: "\033[1;91m",
}
RESET_CODE = "\033[0m"


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        color_code = COLOR_CODES.get(record.levelno, "")
        message = super().format(record)
        return f"{color_code}{message}{RESET_CODE}"


handler = logging.StreamHandler()
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = ColoredFormatter('[{asctime}] [{levelname:<7}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)

logger = logging.getLogger("dankmemer")
logger.setLevel(logging.INFO)
logger.addHandler(handler)


class DankMemerClient:
    """
    An asynchronous client for accessing the DankAlert API.

    This client manages and provides access to various API endpoints
    (e.g. items, npcs, skills, tools) along with built-in caching. In addition, it supports
    anti-rate-limit behavior: when 'useAntirateLimit' is enabled (the default), the client
    ensures that no more than 10 requests are made every 10 seconds.

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

        # Rate-limiting (current API: 10 requests per 10 seconds)
        # may be raised dynamically by Cloudflare even if our cap is respected.
        self._rate_limit_lock = asyncio.Lock()
        self.max_requests: int = 10
        self.request_period: float = 10.0
        self._request_times: list[float] = []

        self.items = items.ItemsRoute(self, self.cache_ttl)
        self.npcs = npcs.NPCsRoute(self, self.cache_ttl)

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
                        now - self._request_times[-1]
                    )
                    logger.info(
                        "Internal rate limit reached; waiting for %s seconds",
                        round(wait_time),
                    )
                    await asyncio.sleep(wait_time)
                    now = time.monotonic()
                    self._request_times = [
                        t for t in self._request_times if now - t < self.request_period
                    ]
                self._request_times.append(now)

        url = f"{self.base_url}/{route}"

        
        max_attempts = 5
        attempt = 0
        backoff = 1.0
        max_sleep = 30.0

        while attempt < max_attempts:
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 429 and self.use_anti_ratelimit:
                        retry_after = response.headers.get("Retry-After")
                        sleep_time = (
                            float(retry_after) if retry_after is not None else backoff
                        )
                        sleep_time = min(sleep_time, max_sleep)
                        jitter = sleep_time * random.uniform(0.8, 1.2)
                        logger.warning(
                            "Received 429 response. Attempt %d/%d. Sleeping for %.2f seconds before retrying...",
                            attempt + 1,
                            max_attempts,
                            jitter,
                        )
                        await asyncio.sleep(jitter)
                        attempt += 1
                        backoff *= 2
                        continue

                    if response.status == 404:
                        error_msg = f"Resource not found at route: {route}"
                        logger.error("%s", error_msg)
                        raise NotFoundException(error_msg, status_code=404)
                    elif response.status == 400:
                        error_msg = f"Bad request for route: {route}"
                        logger.error("%s", error_msg)
                        raise BadRequestException(error_msg, status_code=400)
                    elif 500 <= response.status < 600:
                        error_msg = f"Server error at route: {route}"
                        logger.error("%s", error_msg)
                        raise ServerErrorException(
                            error_msg, status_code=response.status
                        )

                    response.raise_for_status()
                    return await response.json()

            except aiohttp.ClientResponseError as e:
                if e.status == 429 and self.use_anti_ratelimit:
                    sleep_time = min(backoff, max_sleep)
                    jitter = sleep_time * random.uniform(0.8, 1.2)
                    logger.warning(
                        "Caught 429 error (attempt %d/%d). Sleeping for %.2f seconds before retrying...",
                        attempt + 1,
                        max_attempts,
                        jitter,
                    )
                    await asyncio.sleep(jitter)
                    attempt += 1
                    backoff *= 2
                    continue
                else:
                    if e.status == 429:
                        logger.error(
                            "Received 429 response; auto rate limit protection is disabled."
                        )
                        raise RateLimitException(
                            "Rate limit hit and auto-retry is disabled.",
                            status_code=429,
                        )
                    if e.status == 404:
                        logger.error("Not found error: %s", str(e))
                        raise NotFoundException(str(e), status_code=e.status)
                    elif e.status == 400:
                        logger.error("Bad request error: %s", str(e))
                        raise BadRequestException(str(e), status_code=e.status)
                    elif 500 <= e.status < 600:
                        logger.error("Server error: %s", str(e))
                        raise ServerErrorException(str(e), status_code=e.status)
                    else:
                        logger.error("HTTP error: %s", str(e))
                        raise DankMemerHTTPException(str(e), status_code=e.status)

        raise RateLimitException(
            "Max retries exceeded due to repeated 429 responses.", status_code=429
        )
