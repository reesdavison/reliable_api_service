from abc import ABC
from collections import deque
from collections.abc import Generator
from contextlib import contextmanager

from app.config import AppConfig
from app.enums import SignTaskStatus
from app.schemas import IntSignTask


class AbstractQueue(ABC):

    def add(self, x: IntSignTask) -> None:
        pass

    @contextmanager
    def get(self) -> Generator[IntSignTask | None, None, None]:
        pass

    def __len__(self) -> int:
        pass


class InMemoryQueue(AbstractQueue):

    def __init__(self):
        self.queue = deque([])

    def add(self, x: IntSignTask) -> None:
        self.queue.appendleft(x)

    @contextmanager
    def get(self) -> Generator[IntSignTask | None, None, None]:
        if len(self.queue):
            item = self.queue[-1]
            yield item
            if item.status == SignTaskStatus.SUCCESS:
                self.queue.pop()
            elif item.status == SignTaskStatus.FAIL:
                self.queue.pop()
            else:
                pass  # just leave it there
        else:
            yield None

    def __len__(self) -> int:
        return len(self.queue)


import persistqueue


class PersistentQueue(AbstractQueue):

    def __init__(self, db_path: str):
        self.queue = persistqueue.SQLiteAckQueue(db_path, auto_commit=True)

    def add(self, x: IntSignTask) -> None:
        self.queue.put(x)

    @contextmanager
    def get(self) -> Generator[IntSignTask | None, None, None]:
        if len(self):
            item = self.queue.get()
            yield item
            if item.status == SignTaskStatus.SUCCESS:
                self.queue.ack(item)
            elif item.status == SignTaskStatus.FAIL:
                self.queue.ack_failed(item)
            else:
                self.queue.nack(item)  # return it to the queue
        else:
            yield None

    def __len__(self) -> int:
        return self.queue.active_size()


def queue_factory(cfg: AppConfig) -> AbstractQueue:
    if cfg.QUEUE_TYPE == "persistent":
        return PersistentQueue(cfg.PERSISTENT_QUEUE_PATH)
    else:
        return InMemoryQueue()
