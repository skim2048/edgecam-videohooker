import time
import threading
from typing import Any
from collections import deque


class Timeout(Exception):

    def __init__(self):
        msg = "No item became available within the specified time frame."
        super().__init__(msg)


class SingleSlotQueue:

    def __init__(self):
        self.mutex = threading.Lock()
        self.not_empty = threading.Condition(self.mutex)
        self._deque = deque()

    def _put(self, item: Any):
        self._deque.append(item)

    def _get(self) -> Any:
        return self._deque.popleft()

    def put(self, item: Any):
        with self.mutex:
            if len(self._deque) >= 1:
                self._get()
            self._put(item)
            self.not_empty.notify()

    def get(self, timeout_sec: float=30.0) -> Any:
        with self.not_empty:
            endtime = time.monotonic() + timeout_sec
            while not self._deque:
                remaining = endtime - time.monotonic()
                if remaining <= 0:
                    raise Timeout
                self.not_empty.wait(remaining)
            item = self._get()
            return item
