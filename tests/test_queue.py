import tempfile
from uuid import uuid4

from app.enums import SignTaskStatus
from app.queue import InMemoryQueue, PersistentQueue
from app.schemas.messages import IntSignTask


def test_in_memory_queue():

    queue = InMemoryQueue()

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
    with queue.get() as top:
        assert top.id == t1.id

    assert len(queue) == 2
    with queue.get() as top:
        top.mark_done()
        assert top.id == t1.id

    assert len(queue) == 1
    with queue.get() as top:
        top.mark_done()
        assert top.id == t2.id

    # exhaust
    assert len(queue) == 0
    with queue.get() as top:
        assert top is None


def test_persistent_queue():
    with tempfile.TemporaryDirectory() as tmpdir:
        queue = PersistentQueue(tmpdir)

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
        with queue.get() as top:
            assert top.id == t1.id

        assert len(queue) == 2
        with queue.get() as top:
            top.mark_done()
            assert top.id == t1.id

        assert len(queue) == 1
        with queue.get() as top:
            top.mark_done()
            assert top.id == t2.id

        # exhaust
        assert len(queue) == 0
        with queue.get() as top:
            assert top is None
