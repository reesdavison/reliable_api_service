import asyncio
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.enums import ServiceManagerStatus
from app.service_manager import UnreliableServiceManager


@pytest.fixture(scope="function")
def triggered_test_manager():
    """Used for internal testing of actual UnreliableServiceManager"""
    manager = UnreliableServiceManager(max_requests_per_minute=60)
    trigger_make_request = asyncio.Event()

    async def mocked_trigger(*args, **kwargs):
        await trigger_make_request.wait()
        return ServiceManagerStatus.ACK, httpx.Response(status_code=200, content="good")

    manager._make_request = AsyncMock(side_effect=mocked_trigger)
    return manager, trigger_make_request


def get_mocked_manager(
    response=(ServiceManagerStatus.ACK, httpx.Response(status_code=200, content="good"))
):
    """Used as a mock in place of UnreliableServiceManager just modelling its interface
    It should return instantly
    """
    manager = MagicMock()

    async def mock_call(method, url):
        return response

    manager.call = AsyncMock(side_effect=mock_call)
    # set to be very small, so trigger controls flow
    manager.time_step = 0.001

    return manager
