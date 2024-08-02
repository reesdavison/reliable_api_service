import asyncio

import pytest

from app.enums import ServiceManagerStatus

from .manager_fixture import triggered_test_manager


@pytest.mark.asyncio
async def test_service_manager_bursts(triggered_test_manager):
    # ensure _make_request takes enough time to ensure lock is acquired
    # for the full time of the other requests to avoid introducing flakiness

    test_manager, trigger_make_request = triggered_test_manager

    # don't await the first one,
    # it will block until trigger_make_request called
    first_coroutine = test_manager.call("GET", url="foo.com")
    first_task = asyncio.create_task(first_coroutine)

    coroutines = [test_manager.call("GET", url="foo.com") for i in range(9)]
    results = await asyncio.gather(*coroutines)

    # first task should block on trigger_make_request.wait()
    # and be released here
    trigger_make_request.set()
    first_result = await first_task

    assert test_manager._make_request.call_count == 1
    assert first_result[0] == ServiceManagerStatus.ACK
    assert all([res[0] == ServiceManagerStatus.BUSY for res in results])

    # sleep time step amount to
    await asyncio.sleep(test_manager.time_step)

    # perform the same again with 1000 requests
    first_coroutine = test_manager.call("GET", url="foo.com")
    first_task = asyncio.create_task(first_coroutine)
    coroutines = [test_manager.call("GET", url="foo.com") for i in range(999)]
    results = await asyncio.gather(*coroutines)
    trigger_make_request.set()
    first_result = await first_task

    assert test_manager._make_request.call_count == 2
    assert first_result[0] == ServiceManagerStatus.ACK
    assert all([res[0] == ServiceManagerStatus.BUSY for res in results])
