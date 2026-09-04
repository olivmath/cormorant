"""Resilient threaded camera capture worker."""

import asyncio
import threading
import time
from datetime import UTC, datetime

import cv2

from src.config import settings
from src.counter import FootfallCounter
from src.database import get_stats, insert_event, update_camera_status
from src.schemas import LiveUpdate


class _LivePayload(dict):
    """JSON payload that also exposes fields for lightweight integrations."""
    __getattr__ = dict.__getitem__


class CameraWorker(threading.Thread):
    def __init__(self, camera_config, manager) -> None:
        super().__init__(daemon=True)
        self.camera_config = camera_config
        self.manager = manager
        self.counter = FootfallCounter(camera_config.line_start, camera_config.line_end)
        self.stop_event = threading.Event()
        self._stop_event = self.stop_event

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        while not self._stop_event.is_set():
            capture = cv2.VideoCapture(self.camera_config.index, cv2.CAP_AVFOUNDATION)
            if not capture.isOpened():
                self._offline()
                continue
            update_camera_status(self.camera_config.camera_id, self.camera_config.label, True)
            self._read_camera(capture)
            capture.release()
            self._offline()

    def _read_camera(self, capture) -> None:
        frame_number = 0
        while not self._stop_event.is_set():
            ok, frame = capture.read()
            if not ok:
                return
            frame_number += 1
            if frame_number % settings.process_every_n_frames == 0:
                self._process(frame)

    def _process(self, frame) -> None:
        for crossing in self.counter.process_frame(frame):
            event = insert_event(crossing["direction"], self.camera_config.camera_id,
                                 crossing["tracker_id"], crossing["confidence"])
            try:
                stats = get_stats()
                count_in, count_out = stats.count_in, stats.count_out
            except Exception:
                count_in = count_out = 0
            update = LiveUpdate(direction=crossing["direction"], camera_id=self.camera_config.camera_id,
                                timestamp=getattr(event, "timestamp", datetime.now(UTC)),
                                today_in=count_in, today_out=count_out)
            self._broadcast(_LivePayload(update.model_dump(mode="json")))

    def _broadcast(self, message: dict) -> None:
        try:
            asyncio.run(self.manager.broadcast(message))
        except RuntimeError:
            return

    def _offline(self) -> None:
        update_camera_status(self.camera_config.camera_id, self.camera_config.label, False)
        if not self._stop_event.is_set():
            time.sleep(5)
