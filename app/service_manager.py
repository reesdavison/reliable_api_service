import asyncio
import logging
import time

# from collections.abc import Callable, Generator
import httpx

from app.enums import ServiceManagerStatus
from app.logging import get_logger

logger = get_logger(__name__)


class UnreliableServiceManager:

    def __init__(self, headers: dict[str, str] = {}, max_requests_per_minute: int = 10):
        self.time_step = 60.0 / max_requests_per_minute
        self.client = httpx.AsyncClient(headers=headers)
        self.last_time = time.time() - (self.time_step * 1.1)
        self.lock = asyncio.Lock()

    async def _make_request(self, method: str, url: str, *args, **kwargs):
        logger.debug(f"Making external request to {url}")
        try:
            resp = await self.client.request(method=method, url=url, *args, **kwargs)
        except httpx.RequestError:
            logger.exception(f"Error connecting to {url}")

        logger.debug(f"Response status={resp.status_code}, content={resp.content}")
        return resp

    async def call(
        self, method: str, url: str, *args, **kwargs
    ) -> tuple[ServiceManagerStatus, httpx.Response | None]:
        # note: this lock is not thread safe
        # should be fine with a single threaded event loop
        cur_time = time.time()
        if cur_time > self.last_time + self.time_step and not self.lock.locked():
            async with self.lock:
                res = await self._make_request(method=method, url=url, *args, **kwargs)
                self.last_time = time.time()
                # self._handle_result(res)
                return ServiceManagerStatus.ACK, res

        # self._handle_unavailable()
        return ServiceManagerStatus.BUSY, None

    async def cleanup(self):
        await self.client.aclose()
