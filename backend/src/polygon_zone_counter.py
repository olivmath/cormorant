"""Line-crossing via a polygon ROI (shapely) instead of a hairline, reusing supervision's
ByteTrack so this engine isolates the crossing-decision GEOMETRY as the tested variable
rather than also varying the tracker (that comparison already lives in centroid_counter.py
and iou_sort_counter.py).
"""

import logging

try:  # Keep database/API startup usable when vision extras are not installed.
    import supervision as sv
    from shapely.geometry import Point, Polygon
except ModuleNotFoundError:  # pragma: no cover - exercised through mocked integrations
    sv = None
    Point = None
    Polygon = None

from src.config import settings
from src.detector import DEFAULT_DETECTOR, load_model
from src.inference_size import DEFAULT_INFERENCE_SIZE, resolve_imgsz

logger = logging.getLogger(__name__)

BAND_HALF_WIDTH_PX = 40  # same "widen the line into a band" idea as solutions_counter.py


def _band_region(line_start: tuple[int, int], line_end: tuple[int, int]) -> list[tuple[int, int]]:
    dx, dy = line_end[0] - line_start[0], line_end[1] - line_start[1]
    length = max((dx ** 2 + dy ** 2) ** 0.5, 1e-6)
    ox, oy = -dy / length * BAND_HALF_WIDTH_PX, dx / length * BAND_HALF_WIDTH_PX
    return [
        (int(line_start[0] + ox), int(line_start[1] + oy)),
        (int(line_end[0] + ox), int(line_end[1] + oy)),
        (int(line_end[0] - ox), int(line_end[1] - oy)),
        (int(line_start[0] - ox), int(line_start[1] - oy)),
    ]


def _side(point: tuple[float, float], line_start: tuple[int, int], line_end: tuple[int, int]) -> int:
    """Same sign convention as supervision.LineZone: positive (left of start->end) = IN, negative = OUT."""
    x1, y1 = line_start
    x2, y2 = line_end
    cross = (x2 - x1) * (point[1] - y1) - (y2 - y1) * (point[0] - x1)
    return 1 if cross > 0 else (-1 if cross < 0 else 0)


class PolygonZoneCounter:
    def __init__(self, line_start: tuple[int, int], line_end: tuple[int, int],
                 detector_name: str = DEFAULT_DETECTOR, inference_size: str = DEFAULT_INFERENCE_SIZE,
                 band_half_width_px: float = BAND_HALF_WIDTH_PX) -> None:
        if sv is None or Polygon is None:
            raise RuntimeError("Install ultralytics, supervision and shapely to use PolygonZoneCounter")
        self.detector_name = detector_name
        self.inference_size = inference_size
        self._imgsz = resolve_imgsz(inference_size)
        self.model = load_model(detector_name)
        self.tracker = sv.ByteTrack()
        self.band_half_width_px = band_half_width_px
        self.line_start = line_start
        self.line_end = line_end
        self._polygon = Polygon(_band_region(line_start, line_end))
        self._prev_side: dict[int, int] = {}
        self._inside: dict[int, bool] = {}
        self._frame_count = 0
        self.last_people_count = 0
        self.last_tracked_people_count = 0

    def update_line(self, line_start: tuple[int, int], line_end: tuple[int, int]) -> None:
        # supervision's ByteTrack matches purely on IOU/appearance in image space per-frame —
        # unlike ultralytics' ObjectCounter (GMC motion compensation), it has no persistent
        # frame-size-dependent buffer, so it does NOT need to be rebuilt here.
        logger.info("cormorant.polygon_zone_counter.line_updated line_start=%s line_end=%s", line_start, line_end)
        self.line_start = line_start
        self.line_end = line_end
        self._polygon = Polygon(_band_region(line_start, line_end))
        self._prev_side.clear()
        self._inside.clear()

    def process_frame(self, frame) -> list[dict]:
        self._frame_count += 1
        results = self.model(frame, verbose=False, imgsz=self._imgsz)
        detections = sv.Detections.from_ultralytics(results[0])
        class_ids = detections.class_id
        people = [value == 0 for value in class_ids] if isinstance(class_ids, list) else class_ids == 0
        detections = detections[people]
        confidences = detections.confidence
        confident = ([value >= settings.confidence_threshold for value in confidences]
                     if isinstance(confidences, list) else confidences >= settings.confidence_threshold)
        detections = detections[confident]
        self.last_people_count = len(detections)
        detections = self.tracker.update_with_detections(detections)
        self.last_tracked_people_count = len(detections)

        events: list[dict] = []
        for i in range(len(detections)):
            x1, y1, x2, y2 = (float(v) for v in detections.xyxy[i])
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            track_id = int(detections.tracker_id[i])
            is_inside = self._polygon.contains(Point(cx, cy))
            side = _side((cx, cy), self.line_start, self.line_end)

            if self.last_tracked_people_count > 0 and self._frame_count % 15 == 0 and i == 0:
                logger.info(
                    "🚶 [%s/polygon] pessoa vista: posição x=%.0f,y=%.0f | %s | %s",
                    self.detector_name, cx, cy,
                    "dentro do polígono ✅" if is_inside else "fora do polígono",
                    "à direita da linha ➡️" if side > 0 else "⬅️ à esquerda da linha",
                )

            prev_side = self._prev_side.get(track_id)
            was_inside = self._inside.get(track_id, False)
            if prev_side is not None and prev_side != 0 and side != 0 and side != prev_side and (is_inside or was_inside):
                direction = "IN" if side > 0 else "OUT"
                events.append({"direction": direction, "tracker_id": track_id,
                              "confidence": float(detections.confidence[i])})
                emoji = "ENTROU (IN)" if direction == "IN" else "SAIU (OUT)"
                logger.info("✅ [polygon] %s — id=%s", emoji, track_id)

            self._prev_side[track_id] = side
            self._inside[track_id] = is_inside

        return events
