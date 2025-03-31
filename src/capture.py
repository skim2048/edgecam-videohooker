import time
import threading

import cv2
import numpy as np
from loguru import logger

from src.buffer import SingleSlotQueue, Timeout
from src.task import SingleThreadTask


class FailedOpen(Exception):

    def __init__(self):
        msg = "Failed to open the video source."
        super().__init__(msg)


class _Capture:

    def __init__(self):
        self.mutex = threading.Lock()
        self._capture = cv2.VideoCapture()
        self._capture.setExceptionMode(enable=True)

    def open(self, source, api_preference=cv2.CAP_ANY):
        try:
            with self.mutex:
                self._capture.open(source, api_preference)
        except Exception as e:
            raise FailedOpen from e

    def close(self):
        with self.mutex:
            self._capture.release()

    def read(self, timeout_sec: float=30.0) -> np.ndarray:
        endtime = time.monotonic() + timeout_sec
        while True:
            try:
                with self.mutex:
                    _, frame = self._capture.read()
                return frame
            except Exception as e:
                remaining = endtime - time.monotonic()
                if remaining <= 0:
                    raise Timeout from e
                time.sleep(0.1)


class VideoCapture:
    
    def __init__(self):
        self._capture = _Capture()
        self._buffer = SingleSlotQueue()
        self._buffering_task = SingleThreadTask()

    def _buffering(self):
        self._buffer.put(self._capture.read())

    def open(self, source, api_preference=cv2.CAP_ANY):
        self._capture.open(source, api_preference)
        if self._buffering_task.is_alive():
            self._buffering_task.stop()
        self._buffering_task.start(self._buffering)

    def close(self):
        if self._buffering_task.is_alive():
            self._buffering_task.stop()
        self._capture.close()

    def read(self, timeout_sec=30.0) -> np.ndarray:
        try:
            frame = self._buffer.get(timeout_sec)
        except Timeout as e:
            logger.exception("Timeout occurred while reading from buffer")
            self.close()
        else:
            return frame
