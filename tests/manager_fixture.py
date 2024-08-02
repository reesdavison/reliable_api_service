import asyncio
from unittest.mock import AsyncMock

import httpx
import pytest

from app.enums import ServiceManagerStatus
from app.service_manager import UnreliableServiceManager


@pytest.fixture(scope="function")
def triggered_test_manager():
    manager = UnreliableServiceManager(max_requests_per_minute=60)
    trigger_make_request = asyncio.Event()

    async def mocked_trigger(*args, **kwargs):
        await trigger_make_request.wait()
        return ServiceManagerStatus.ACK, httpx.Response(status_code=200, content="good")

    manager._make_request = AsyncMock(side_effect=mocked_trigger)
    return manager, trigger_make_request


@pytest.fixture(scope="function")
def test_manager():
    manager = UnreliableServiceManager(max_requests_per_minute=60)
    manager._make_request = AsyncMock()
    return manager
