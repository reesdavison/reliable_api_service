import asyncio
import time

import httpx


class UnreliableServiceManager:

    def __init__(self, headers: dict[str, str] = {}, max_requests_per_minute: int = 10):
        self.time_step = 60.0 / max_requests_per_minute
        self.client = httpx.AsyncClient()
        self.last_time = time.time() - (self.time_step * 1.1)
        self.lock = asyncio.Lock()

    def _handle_result(self, response: httpx.Response):
        pass

    def _handle_unavailable(self, method: str, *args, **kwargs):
        pass

    async def _make_request(self, method: str, *args, **kwargs):
        return await self.client.request(method=method, *args, **kwargs)

    async def call(self, method: str, *args, **kwargs):
        # note: this lock is not thread safe
        cur_time = time.time()
        if cur_time > self.last_time + self.time_step and not self.lock.locked():
            async with self.lock:
                res = await self._make_request(method=method, *args, **kwargs)
                self.last_time = time.time()
                self._handle_result(res)
                return

        self._handle_unavailable()

    async def cleanup(self):
        await self.client.aclose()
