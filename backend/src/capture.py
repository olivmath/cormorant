"""Resilient threaded camera capture worker."""

import asyncio
import logging
import sys
import threading
import time
from datetime import UTC, datetime

import cv2

from src.config import settings
from src.counting import create_counter
from src.database import (
    get_counting_engine,
    get_detector_model,
    get_inference_size,
    get_stats,
    insert_event,
    update_camera_status,
)
from src.schemas import LiveUpdate

logger = logging.getLogger(__name__)

if sys.platform == "darwin":
    _CAPTURE_BACKEND = cv2.CAP_AVFOUNDATION
elif sys.platform.startswith("linux"):
    _CAPTURE_BACKEND = cv2.CAP_V4L2
else:
    _CAPTURE_BACKEND = cv2.CAP_ANY


class _LivePayload(dict):
    """JSON payload that also exposes fields for lightweight integrations."""
    __getattr__ = dict.__getitem__


class CameraWorker(threading.Thread):
    def __init__(self, camera_config, manager) -> None:
        super().__init__(daemon=True)
        self.camera_config = camera_config
        self.manager = manager
        self.counter = create_counter(camera_config.line_start, camera_config.line_end,
                                      get_detector_model(), get_counting_engine(), get_inference_size())
        self.stop_event = threading.Event()
        self._stop_event = self.stop_event

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        logger.info("cormorant.capture.starting camera_id=%s label=%s", self.camera_config.camera_id, self.camera_config.label)
        while not self._stop_event.is_set():
            capture = cv2.VideoCapture(self.camera_config.index, _CAPTURE_BACKEND)
            if not capture.isOpened():
                logger.warning("cormorant.capture.open_failed camera_id=%s index=%s", self.camera_config.camera_id, self.camera_config.index)
                self._offline()
                continue
            logger.info("cormorant.capture.connected camera_id=%s", self.camera_config.camera_id)
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
        detector_name = get_detector_model()
        engine = get_counting_engine()
        inference_size = get_inference_size()
        if (detector_name != self.counter.detector_name or engine != self.counter.engine
                or inference_size != self.counter.inference_size):
            logger.info("🔄 câmera %s trocando engine/modelo/tamanho: %s/%s/%s → %s/%s/%s",
                       self.camera_config.camera_id, self.counter.engine, self.counter.detector_name,
                       self.counter.inference_size, engine, detector_name, inference_size)
            self.counter = create_counter(self.counter.line_start, self.counter.line_end,
                                          detector_name, engine, inference_size)
        crossings = self.counter.process_frame(frame)
        if crossings:
            logger.info(
                "cormorant.capture.crossings camera_id=%s count=%s directions=%s",
                self.camera_config.camera_id, len(crossings),
                [c["direction"] for c in crossings],
            )
        for crossing in crossings:
            event = insert_event(crossing["direction"], self.camera_config.camera_id,
                                 crossing["tracker_id"], crossing["confidence"])
            try:
                stats = get_stats()
                count_in, count_out = stats.count_in, stats.count_out
            except Exception:
                count_in = count_out = 0
            logger.info(
                "cormorant.capture.event_saved direction=%s camera_id=%s tracker_id=%s today_in=%s today_out=%s",
                crossing["direction"], self.camera_config.camera_id,
                crossing["tracker_id"], count_in, count_out,
            )
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
