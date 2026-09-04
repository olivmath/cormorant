"""Classic PyImageSearch-style centroid tracker: no ByteTrack/BoT-SORT, no motion model,
just greedy nearest-neighbor matching of detection centroids between consecutive frames.

Deliberately dependency-free (no scipy Hungarian assignment): at doorway-camera cardinality
(usually 1-3 people at once) a sorted-distance greedy match is effectively as good as an
optimal assignment and costs nothing extra to install.
"""

import logging

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


class CentroidCounter:
    def __init__(self, line_start: tuple[int, int], line_end: tuple[int, int],
                 detector_name: str = DEFAULT_DETECTOR, inference_size: str = DEFAULT_INFERENCE_SIZE,
                 max_disappeared: int = 10, max_distance_px: float = 120.0) -> None:
        self.detector_name = detector_name
        self.inference_size = inference_size
        self._imgsz = resolve_imgsz(inference_size)
        self.model = load_model(detector_name)
        self.line_start = line_start
        self.line_end = line_end
        self.max_disappeared = max_disappeared
        self.max_distance_px = max_distance_px
        self._objects: dict[int, tuple[float, float]] = {}
        self._disappeared: dict[int, int] = {}
        self._sides: dict[int, int] = {}
        self._next_id = 0
        self._frame_count = 0
        self.last_people_count = 0
        self.last_tracked_people_count = 0

    def update_line(self, line_start: tuple[int, int], line_end: tuple[int, int]) -> None:
        """Geometry changed (calibration or stream resolution) — old side-of-line history is meaningless."""
        logger.info("cormorant.centroid_counter.line_updated line_start=%s line_end=%s", line_start, line_end)
        self.line_start = line_start
        self.line_end = line_end
        self._objects.clear()
        self._disappeared.clear()
        self._sides.clear()

    def process_frame(self, frame) -> list[dict]:
        self._frame_count += 1
        results = self.model(frame, verbose=False, imgsz=self._imgsz)
        boxes = results[0].boxes
        centroids: list[tuple[float, float]] = []
        confidences: list[float] = []
        for box, cls_id, conf in zip(boxes.xyxy, boxes.cls, boxes.conf):
            if int(cls_id) != PERSON_CLASS_ID or float(conf) < settings.confidence_threshold:
                continue
            x1, y1, x2, y2 = (float(v) for v in box)
            centroids.append(((x1 + x2) / 2, (y1 + y2) / 2))
            confidences.append(float(conf))
        self.last_people_count = len(centroids)

        matched_ids, _new_ids = self._match(centroids)
        self.last_tracked_people_count = len(self._objects)

        if self.last_tracked_people_count > 0 and self._frame_count % 15 == 0:
            any_id = next(iter(self._objects))
            cx, _ = self._objects[any_id]
            line_x = (self.line_start[0] + self.line_end[0]) / 2
            logger.info(
                "🚶 [%s/centroid] pessoa vista: posição x=%.0f | linha em x=%.0f | %s",
                self.detector_name, cx, line_x,
                "à direita da linha ➡️" if cx > line_x else "⬅️ à esquerda da linha",
            )

        events: list[dict] = []
        for track_id, centroid_index in matched_ids.items():
            new_side = _side(centroids[centroid_index], self.line_start, self.line_end)
            old_side = self._sides.get(track_id)
            if old_side is not None and old_side != 0 and new_side != 0 and new_side != old_side:
                direction = "IN" if new_side > 0 else "OUT"
                events.append({"direction": direction, "tracker_id": track_id,
                              "confidence": confidences[centroid_index]})
                emoji = "ENTROU (IN)" if direction == "IN" else "SAIU (OUT)"
                logger.info("✅ [centroid] %s — id=%s", emoji, track_id)
            self._sides[track_id] = new_side
        return events

    def _match(self, centroids: list[tuple[float, float]]) -> tuple[dict[int, int], list[int]]:
        existing_ids = list(self._objects.keys())
        pairs = [
            (track_id, index, self._distance(self._objects[track_id], centroids[index]))
            for track_id in existing_ids
            for index in range(len(centroids))
        ]
        pairs.sort(key=lambda item: item[2])

        claimed_tracks: set[int] = set()
        claimed_centroids: set[int] = set()
        matched: dict[int, int] = {}
        for track_id, index, distance in pairs:
            if track_id in claimed_tracks or index in claimed_centroids:
                continue
            if distance > self.max_distance_px:
                continue
            claimed_tracks.add(track_id)
            claimed_centroids.add(index)
            matched[track_id] = index
            self._objects[track_id] = centroids[index]
            self._disappeared[track_id] = 0

        for track_id in existing_ids:
            if track_id not in claimed_tracks:
                self._disappeared[track_id] = self._disappeared.get(track_id, 0) + 1
                if self._disappeared[track_id] > self.max_disappeared:
                    del self._objects[track_id]
                    self._disappeared.pop(track_id, None)
                    self._sides.pop(track_id, None)

        new_ids = []
        for index in range(len(centroids)):
            if index in claimed_centroids:
                continue
            self._next_id += 1
            track_id = self._next_id
            self._objects[track_id] = centroids[index]
            self._disappeared[track_id] = 0
            matched[track_id] = index
            new_ids.append(track_id)

        return matched, new_ids

    @staticmethod
    def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
