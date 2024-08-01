from collections import deque

from app.schemas import SignTask


class InMemoryQueue:

    def __init__(self):
        self.queue = deque([])

    def add(self, x: SignTask):
        self.queue.appendleft(x)

    def peak(self):
        return self.queue[-1]

    def pop(self):
        return self.queue.pop()
