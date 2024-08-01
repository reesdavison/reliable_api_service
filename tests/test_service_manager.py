import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.service_manager import UnreliableServiceManager


@pytest.fixture(scope="function")
def get_test_manager():
    manager = UnreliableServiceManager(max_requests_per_minute=60)
    # manager._handle_result = MagicMock()
    # manager._handle_unavailable = MagicMock()

    trigger_make_request = asyncio.Event()

    async def mocked_trigger(*args, **kwargs):
        await trigger_make_request.wait()

    manager._make_request = AsyncMock(side_effect=mocked_trigger)
    return manager, trigger_make_request


@pytest.mark.asyncio
async def test_service_manager_bursts(get_test_manager):
    # ensure _make_request takes enough time to ensure lock is acquired
    # for the full time of the other requests to avoid introducing flakiness

    test_manager, trigger_make_request = get_test_manager

    # don't await the first one,
    # it will block until trigger_make_request called
    first_coroutine = test_manager.call("GET", url="foo.com")
    first_task = asyncio.create_task(first_coroutine)

    coroutines = [test_manager.call("GET", url="foo.com") for i in range(9)]
    results = await asyncio.gather(*coroutines)

    # first task should block on trigger_make_request.wait()
    # and be released here
    trigger_make_request.set()
    await first_task

    assert test_manager._handle_result.call_count == 1
    assert test_manager._make_request.call_count == 1
    assert test_manager._handle_unavailable.call_count == 9

    # sleep time step amount to
    await asyncio.sleep(test_manager.time_step)

    # perform the same again with 1000 requests
    first_coroutine = test_manager.call("GET", url="foo.com")
    first_task = asyncio.create_task(first_coroutine)
    coroutines = [test_manager.call("GET", url="foo.com") for i in range(999)]
    await asyncio.gather(*coroutines)
    trigger_make_request.set()
    await first_task

    assert test_manager._handle_result.call_count == 1 + 1
    assert test_manager._make_request.call_count == 1 + 1
    assert test_manager._handle_unavailable.call_count == 9 + 999
