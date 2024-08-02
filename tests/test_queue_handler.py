import asyncio
import base64
import copy
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import httpx
import pytest

from app.enums import ServiceManagerStatus, SignTaskStatus
from app.main import queue_handler
from app.queue import InMemoryQueue
from app.schemas.messages import IntSignTask


@pytest.mark.asyncio
async def test_queue_handler_success():

    queue = InMemoryQueue()
    manager = MagicMock()

    async def mock_call(method, url):
        return ServiceManagerStatus.ACK, httpx.Response(
            status_code=200, content=b"aaaa"
        )

    manager.call = AsyncMock(side_effect=mock_call)
    manager.time_step = 1
    on_success = AsyncMock()

    task = asyncio.create_task(queue_handler("foo.com", queue, manager, on_success))

    t1 = IntSignTask(
        webhook_url="foo.foo.foo.1",
        message="foobar1",
        id=uuid4(),
        status=SignTaskStatus.PENDING,
    )
    t2 = IntSignTask(
        webhook_url="foo.foo.foo.2",
        message="foobar2",
        id=uuid4(),
        status=SignTaskStatus.PENDING,
    )
    t3 = IntSignTask(
        webhook_url="foo.foo.foo.3",
        message="foobar3",
        id=uuid4(),
        status=SignTaskStatus.PENDING,
    )
    queue.add(t1)
    queue.add(t2)
    await asyncio.sleep(1)

    exp_task = copy.deepcopy(t1)
    exp_task.status = SignTaskStatus.SUCCESS
    exp_task.signature = base64.b64encode(b"aaaa").decode("ascii")

    assert manager.call.call_count == 1
    assert on_success.call_count == 1
    assert on_success.call_args[0][0] == exp_task
    assert len(queue) == 1
    assert queue.peak() == t2

    # add another item to the queue and sleep so queue handler can resume
    queue.add(t3)
    await asyncio.sleep(1)

    exp_task = copy.deepcopy(t2)
    exp_task.status = SignTaskStatus.SUCCESS
    exp_task.signature = base64.b64encode(b"aaaa").decode("ascii")

    assert manager.call.call_count == 2
    assert on_success.call_count == 2
    assert on_success.call_args[0][0] == exp_task
    assert len(queue) == 1
    assert queue.peak() == t3

    task.cancel()


@pytest.mark.asyncio
async def test_queue_handler_busy_and_growing_queue():

    queue = InMemoryQueue()
    manager = MagicMock()

    async def mock_call(method, url):
        return ServiceManagerStatus.BUSY, None

    manager.call = AsyncMock(side_effect=mock_call)
    manager.time_step = 1
    on_success = AsyncMock()

    task = asyncio.create_task(queue_handler("foo.com", queue, manager, on_success))

    t1 = IntSignTask(
        webhook_url="foo.foo.foo.1",
        message="foobar1",
        id=uuid4(),
        status=SignTaskStatus.PENDING,
    )
    t2 = IntSignTask(
        webhook_url="foo.foo.foo.2",
        message="foobar2",
        id=uuid4(),
        status=SignTaskStatus.PENDING,
    )
    t3 = IntSignTask(
        webhook_url="foo.foo.foo.3",
        message="foobar3",
        id=uuid4(),
        status=SignTaskStatus.PENDING,
    )
    queue.add(t1)
    queue.add(t2)
    await asyncio.sleep(1)

    assert manager.call.call_count == 1
    assert on_success.call_count == 0
    assert len(queue) == 2
    assert queue.peak() == t1

    # add another item to the queue and sleep so queue handler can resume
    queue.add(t3)
    await asyncio.sleep(1)

    assert manager.call.call_count == 2
    assert on_success.call_count == 0
    assert len(queue) == 3
    assert queue.peak() == t1

    task.cancel()


@pytest.mark.asyncio
async def test_queue_handler_ack_but_bad_status():

    queue = InMemoryQueue()
    manager = MagicMock()

    async def mock_call(method, url):
        return ServiceManagerStatus.ACK, httpx.Response(
            status_code=500, content="denied"
        )

    manager.call = AsyncMock(side_effect=mock_call)
    manager.time_step = 1
    on_success = AsyncMock()

    task = asyncio.create_task(queue_handler("foo.com", queue, manager, on_success))

    t1 = IntSignTask(
        webhook_url="foo.foo.foo.1",
        message="foobar1",
        id=uuid4(),
        status=SignTaskStatus.PENDING,
    )
    t2 = IntSignTask(
        webhook_url="foo.foo.foo.2",
        message="foobar2",
        id=uuid4(),
        status=SignTaskStatus.PENDING,
    )
    t3 = IntSignTask(
        webhook_url="foo.foo.foo.3",
        message="foobar3",
        id=uuid4(),
        status=SignTaskStatus.PENDING,
    )
    queue.add(t1)
    queue.add(t2)
    await asyncio.sleep(1)

    assert manager.call.call_count == 1
    assert on_success.call_count == 0
    assert len(queue) == 2
    assert queue.peak() == t1

    # add another item to the queue and sleep so queue handler can resume
    queue.add(t3)
    await asyncio.sleep(1)

    assert manager.call.call_count == 2
    assert on_success.call_count == 0
    assert len(queue) == 3
    assert queue.peak() == t1

    task.cancel()


@pytest.mark.asyncio
async def test_queue_handler_max_retries():

    queue = InMemoryQueue()
    manager = MagicMock()

    trigger_call = asyncio.Event()

    async def mock_call(method, url):
        await trigger_call.wait()
        return ServiceManagerStatus.ACK, httpx.Response(
            status_code=500, content="denied"
        )

    manager.call = AsyncMock(side_effect=mock_call)
    # set to be very small, so sleeps in here control flow
    manager.time_step = 0.001
    on_success = AsyncMock()

    max_retries = 2
    task = asyncio.create_task(
        queue_handler("foo.com", queue, manager, on_success, max_retries)
    )

    t1 = IntSignTask(
        webhook_url="foo.foo.foo.1",
        message="foobar1",
        id=uuid4(),
        status=SignTaskStatus.PENDING,
    )
    t2 = IntSignTask(
        webhook_url="foo.foo.foo.2",
        message="foobar2",
        id=uuid4(),
        status=SignTaskStatus.PENDING,
    )
    queue.add(t1)
    queue.add(t2)
    await asyncio.sleep(1)

    assert manager.call.call_count == 1
    assert on_success.call_count == 0
    assert len(queue) == 2
    assert queue.peak() == t1

    # allow queue handler to run
    # this seems to trigger the behaviour I'm after
    # TODO check this is the most idiomatic way to handle this
    trigger_call.set()
    trigger_call.clear()
    await asyncio.sleep(1.0)

    assert manager.call.call_count == 2
    assert on_success.call_count == 0
    assert len(queue) == 2
    assert queue.peak() == t1

    # allow queue handler to run
    trigger_call.set()
    trigger_call.clear()
    await asyncio.sleep(1.0)

    # the top t1 should be cleared from the queue
    # t2 is now on top
    assert manager.call.call_count == 3
    assert on_success.call_count == 0
    assert len(queue) == 1
    assert queue.peak() == t2

    task.cancel()
