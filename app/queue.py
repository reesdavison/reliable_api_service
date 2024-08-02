from collections import deque

from app.schemas import IntSignTask


class InMemoryQueue:

    def __init__(self):
        self.queue = deque([])

    def add(self, x: IntSignTask):
        self.queue.appendleft(x)

    def peak(self) -> IntSignTask | None:
        if len(self.queue):
            return self.queue[-1]
        return None

    def pop(self):
        return self.queue.pop()

    def __len__(self):
        return len(self.queue)
