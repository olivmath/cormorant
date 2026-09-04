"""ByteTrack + line, but a crossing only confirms after a track has stayed continuously on
one side for at least `min_dwell_frames` processed frames — filters flicker-driven false
positives at the cost of slightly delayed confirmation. Also logs per-crossing dwell time.
"""

import logging

try:  # Keep database/API startup usable when vision extras are not installed.
    import supervision as sv
except ModuleNotFoundError:  # pragma: no cover - exercised through mocked integrations
    sv = None

from src.config import settings
from src.detector import DEFAULT_DETECTOR, load_model
from src.inference_size import DEFAULT_INFERENCE_SIZE, resolve_imgsz

logger = logging.getLogger(__name__)

ASSUMED_FPS = 6  # display-only estimate for human-readable dwell time; never used in the decision logic


def _side(point: tuple[float, float], line_start: tuple[int, int], line_end: tuple[int, int]) -> int:
    """Same sign convention as supervision.LineZone: positive (left of start->end) = IN, negative = OUT."""
    x1, y1 = line_start
    x2, y2 = line_end
    cross = (x2 - x1) * (point[1] - y1) - (y2 - y1) * (point[0] - x1)
    return 1 if cross > 0 else (-1 if cross < 0 else 0)


class DwellDebounceCounter:
    def __init__(self, line_start: tuple[int, int], line_end: tuple[int, int],
                 detector_name: str = DEFAULT_DETECTOR, inference_size: str = DEFAULT_INFERENCE_SIZE,
                 min_dwell_frames: int = 5) -> None:
        if sv is None:
            raise RuntimeError("Install ultralytics and supervision to use DwellDebounceCounter")
        self.detector_name = detector_name
        self.inference_size = inference_size
        self._imgsz = resolve_imgsz(inference_size)
        self.model = load_model(detector_name)
        self.tracker = sv.ByteTrack()
        self.min_dwell_frames = min_dwell_frames
        self.line_start = line_start
        self.line_end = line_end
        self._pending_side: dict[int, int] = {}
        self._pending_since_frame: dict[int, int] = {}
        self._side_history: dict[int, int] = {}
        self._frame_count = 0
        self.last_people_count = 0
        self.last_tracked_people_count = 0

    def update_line(self, line_start: tuple[int, int], line_end: tuple[int, int]) -> None:
        # Temporal continuity is this engine's whole point, so a tracker carrying state from
        # before a geometry change would corrupt dwell timing — rebuild it along with the
        # per-track dwell dicts (unlike polygon_zone_counter.py, which can keep its tracker).
        logger.info("cormorant.dwell_debounce_counter.line_updated line_start=%s line_end=%s", line_start, line_end)
        self.line_start = line_start
        self.line_end = line_end
        self.tracker = sv.ByteTrack()
        self._pending_side.clear()
        self._pending_since_frame.clear()
        self._side_history.clear()

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
            side = _side((cx, cy), self.line_start, self.line_end)

            if self.last_tracked_people_count > 0 and self._frame_count % 15 == 0 and i == 0:
                dwell = self._frame_count - self._pending_since_frame.get(track_id, self._frame_count)
                line_x = (self.line_start[0] + self.line_end[0]) / 2
                logger.info(
                    "🚶 [%s/dwell] pessoa vista: posição x=%.0f | linha em x=%.0f | %s | dwell=%sf",
                    self.detector_name, cx, line_x,
                    "à direita da linha ➡️" if cx > line_x else "⬅️ à esquerda da linha",
                    dwell,
                )

            if self._pending_side.get(track_id) != side:
                self._pending_side[track_id] = side
                self._pending_since_frame[track_id] = self._frame_count
            else:
                dwell_frames = self._frame_count - self._pending_since_frame[track_id]
                if dwell_frames >= self.min_dwell_frames:
                    confirmed_side = self._side_history.get(track_id)
                    if confirmed_side is not None and confirmed_side != side and side != 0:
                        direction = "IN" if side > 0 else "OUT"
                        events.append({"direction": direction, "tracker_id": track_id,
                                      "confidence": float(detections.confidence[i])})
                        emoji = "ENTROU (IN)" if direction == "IN" else "SAIU (OUT)"
                        logger.info(
                            "✅ [dwell] %s — id=%s | permanência=%sf (~%.1fs)",
                            emoji, track_id, dwell_frames, dwell_frames / ASSUMED_FPS,
                        )
                    self._side_history[track_id] = side

        return events
