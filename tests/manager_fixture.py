import asyncio
from unittest.mock import AsyncMock

import pytest

from app.service_manager import UnreliableServiceManager


@pytest.fixture(scope="function")
def triggered_test_manager():
    manager = UnreliableServiceManager(max_requests_per_minute=60)
    trigger_make_request = asyncio.Event()

    async def mocked_trigger(*args, **kwargs):
        await trigger_make_request.wait()

    manager._make_request = AsyncMock(side_effect=mocked_trigger)
    return manager, trigger_make_request


@pytest.fixture(scope="function")
def test_manager():
    manager = UnreliableServiceManager(max_requests_per_minute=60)
    manager._make_request = AsyncMock()
    return manager
