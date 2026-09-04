"""Minimal SORT-style tracker: IOU matching + linear (2-point) motion extrapolation.

Deliberately NOT a real Kalman filter — no covariance/uncertainty modeling, just
`predicted = box + (box - prev_box)`. This mirrors the "runs fine on a Raspberry Pi"
design goal of the source project it's modeled after: numpy-only, no scipy/filterpy.
"""

import logging

import numpy as np

from src.config import settings
from src.detector import DEFAULT_DETECTOR, load_model
from src.inference_size import DEFAULT_INFERENCE_SIZE, resolve_imgsz

logger = logging.getLogger(__name__)

PERSON_CLASS_ID = 0


def _side(point: tuple[float, float], line_start: tuple[int, int], line_end: tuple[int, int]) -> int:
    """Same sign convention as supervision.LineZone: positive (left of start->end) = IN, negative = OUT."""
    x1, y1 = line_start
    x2, y2 = line_end
    cross = (x2 - x1) * (point[1] - y1) - (y2 - y1) * (point[0] - x1)
    return 1 if cross > 0 else (-1 if cross < 0 else 0)


def _iou(box_a: np.ndarray, box_b: np.ndarray) -> float:
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])
    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    if intersection == 0:
        return 0.0
    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    return intersection / (area_a + area_b - intersection)


class _Track:
    def __init__(self, box: np.ndarray):
        self.box = box
        self.prev_box = box
        self.velocity = np.zeros(4)
        self.hits = 1
        self.age = 0
        self.side = 0

    def predicted_box(self) -> np.ndarray:
        return self.box + self.velocity

    def update(self, box: np.ndarray) -> None:
        self.prev_box = self.box
        self.box = box
        self.velocity = self.box - self.prev_box
        self.hits += 1
        self.age = 0

    def center(self) -> tuple[float, float]:
        return ((self.box[0] + self.box[2]) / 2, (self.box[1] + self.box[3]) / 2)


class IouSortCounter:
    def __init__(self, line_start: tuple[int, int], line_end: tuple[int, int],
                 detector_name: str = DEFAULT_DETECTOR, inference_size: str = DEFAULT_INFERENCE_SIZE,
                 iou_threshold: float = 0.3, min_hits: int = 2, max_age: int = 8) -> None:
        self.detector_name = detector_name
        self.inference_size = inference_size
        self._imgsz = resolve_imgsz(inference_size)
        self.model = load_model(detector_name)
        self.line_start = line_start
        self.line_end = line_end
        self.iou_threshold = iou_threshold
        self.min_hits = min_hits
        self.max_age = max_age
        self._tracks: dict[int, _Track] = {}
        self._next_id = 0
        self._frame_count = 0
        self.last_people_count = 0
        self.last_tracked_people_count = 0

    def update_line(self, line_start: tuple[int, int], line_end: tuple[int, int]) -> None:
        """Geometry changed — stale velocities/side history from before are unreliable."""
        logger.info("cormorant.iou_sort_counter.line_updated line_start=%s line_end=%s", line_start, line_end)
        self.line_start = line_start
        self.line_end = line_end
        self._tracks.clear()

    def process_frame(self, frame) -> list[dict]:
        self._frame_count += 1
        results = self.model(frame, verbose=False, imgsz=self._imgsz)
        boxes = results[0].boxes
        detections: list[np.ndarray] = []
        confidences: list[float] = []
        for box, cls_id, conf in zip(boxes.xyxy, boxes.cls, boxes.conf):
            if int(cls_id) != PERSON_CLASS_ID or float(conf) < settings.confidence_threshold:
                continue
            detections.append(np.array([float(v) for v in box]))
            confidences.append(float(conf))
        self.last_people_count = len(detections)

        matched, new_ids = self._match(detections)
        confirmed = [track_id for track_id, track in self._tracks.items() if track.hits >= self.min_hits]
        self.last_tracked_people_count = len(confirmed)

        if confirmed and self._frame_count % 15 == 0:
            cx, _ = self._tracks[confirmed[0]].center()
            line_x = (self.line_start[0] + self.line_end[0]) / 2
            logger.info(
                "🚶 [%s/iou_sort] pessoa vista: posição x=%.0f | linha em x=%.0f | %s",
                self.detector_name, cx, line_x,
                "à direita da linha ➡️" if cx > line_x else "⬅️ à esquerda da linha",
            )

        events: list[dict] = []
        for track_id, detection_index in matched.items():
            track = self._tracks[track_id]
            if track.hits < self.min_hits:
                continue
            new_side = _side(track.center(), self.line_start, self.line_end)
            old_side = track.side
            if old_side != 0 and new_side != 0 and new_side != old_side:
                direction = "IN" if new_side > 0 else "OUT"
                events.append({"direction": direction, "tracker_id": track_id,
                              "confidence": confidences[detection_index]})
                emoji = "ENTROU (IN)" if direction == "IN" else "SAIU (OUT)"
                logger.info("✅ [iou_sort] %s — id=%s", emoji, track_id)
            track.side = new_side
        return events

    def _match(self, detections: list[np.ndarray]) -> tuple[dict[int, int], list[int]]:
        existing_ids = list(self._tracks.keys())
        pairs = [
            (track_id, index, _iou(self._tracks[track_id].predicted_box(), detections[index]))
            for track_id in existing_ids
            for index in range(len(detections))
        ]
        pairs.sort(key=lambda item: item[2], reverse=True)

        claimed_tracks: set[int] = set()
        claimed_detections: set[int] = set()
        matched: dict[int, int] = {}
        for track_id, index, iou in pairs:
            if track_id in claimed_tracks or index in claimed_detections:
                continue
            if iou < self.iou_threshold:
                continue
            claimed_tracks.add(track_id)
            claimed_detections.add(index)
            matched[track_id] = index
            self._tracks[track_id].update(detections[index])

        for track_id in existing_ids:
            if track_id not in claimed_tracks:
                track = self._tracks[track_id]
                track.age += 1
                if track.age > self.max_age:
                    del self._tracks[track_id]

        new_ids = []
        for index in range(len(detections)):
            if index in claimed_detections:
                continue
            self._next_id += 1
            track_id = self._next_id
            self._tracks[track_id] = _Track(detections[index])
            matched[track_id] = index
            new_ids.append(track_id)

        return matched, new_ids
