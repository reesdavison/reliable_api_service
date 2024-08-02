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

from .manager_fixture import get_mocked_manager

HIGH_RETRIES = 100000


@pytest.mark.asyncio
async def test_queue_handler_success():

    queue = InMemoryQueue()
    manager = get_mocked_manager(
        response=(
            ServiceManagerStatus.ACK,
            httpx.Response(status_code=200, content=b"aaaa"),
        )
    )
    on_success = AsyncMock()

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

    # it should block on await manager.call()
    task = asyncio.create_task(
        queue_handler("foo.com", queue, manager, on_success, HIGH_RETRIES)
    )

    # ensure enough time for tasks to be consumed
    await asyncio.sleep(0.25)

    exp_task = copy.deepcopy(t2)
    exp_task.status = SignTaskStatus.SUCCESS
    exp_task.signature = base64.b64encode(b"aaaa").decode("ascii")

    assert on_success.call_count == 2
    assert on_success.call_args[0][0] == exp_task  # the last task
    assert len(queue) == 0

    # add another item to the queue and sleep so queue handler can resume
    queue.add(t3)
    await asyncio.sleep(0.25)

    exp_task = copy.deepcopy(t3)
    exp_task.status = SignTaskStatus.SUCCESS
    exp_task.signature = base64.b64encode(b"aaaa").decode("ascii")

    assert on_success.call_count == 3
    assert on_success.call_args[0][0] == exp_task
    assert len(queue) == 0

    task.cancel()


@pytest.mark.asyncio
async def test_queue_handler_busy_and_growing_queue():

    queue = InMemoryQueue()

    manager = get_mocked_manager(
        response=(
            ServiceManagerStatus.BUSY,
            None,
        )
    )

    on_success = AsyncMock()

    task = asyncio.create_task(
        queue_handler("foo.com", queue, manager, on_success, HIGH_RETRIES)
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
    t3 = IntSignTask(
        webhook_url="foo.foo.foo.3",
        message="foobar3",
        id=uuid4(),
        status=SignTaskStatus.PENDING,
    )
    queue.add(t1)
    queue.add(t2)
    await asyncio.sleep(0.25)

    assert on_success.call_count == 0
    assert len(queue) == 2
    assert queue.peak() == t1

    # add another item to the queue and sleep so queue handler can resume
    queue.add(t3)
    await asyncio.sleep(0.25)

    assert on_success.call_count == 0
    assert len(queue) == 3
    assert queue.peak() == t1

    task.cancel()


@pytest.mark.asyncio
async def test_queue_handler_ack_but_bad_status():

    queue = InMemoryQueue()

    manager = get_mocked_manager(
        response=(
            ServiceManagerStatus.ACK,
            httpx.Response(status_code=500, content="bad"),
        )
    )

    on_success = AsyncMock()

    task = asyncio.create_task(
        queue_handler("foo.com", queue, manager, on_success, HIGH_RETRIES)
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
    t3 = IntSignTask(
        webhook_url="foo.foo.foo.3",
        message="foobar3",
        id=uuid4(),
        status=SignTaskStatus.PENDING,
    )
    queue.add(t1)
    queue.add(t2)
    await asyncio.sleep(0.25)

    assert on_success.call_count == 0
    assert len(queue) == 2
    assert queue.peak() == t1

    # add another item to the queue and sleep so queue handler can resume
    queue.add(t3)
    await asyncio.sleep(0.25)

    assert on_success.call_count == 0
    assert len(queue) == 3
    assert queue.peak() == t1

    task.cancel()


@pytest.mark.asyncio
async def test_queue_handler_max_retries():

    queue = InMemoryQueue()

    manager = get_mocked_manager(
        response=(
            ServiceManagerStatus.ACK,
            httpx.Response(status_code=500, content="bad"),
        )
    )

    on_success = AsyncMock()

    max_retries = 2

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
    assert len(queue) == 2

    task = asyncio.create_task(
        queue_handler("foo.com", queue, manager, on_success, max_retries)
    )

    await asyncio.sleep(0.25)
    assert on_success.call_count == 0
    assert len(queue) == 0

    task.cancel()
