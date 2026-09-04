"""Person tracking and directional line-crossing detection."""

import logging

try:  # Keep database/API startup usable when vision extras are not installed.
    import supervision as sv
except ModuleNotFoundError:  # pragma: no cover - exercised through mocked integrations
    sv = None

from src.config import settings
from src.detector import DEFAULT_DETECTOR, load_model
from src.inference_size import DEFAULT_INFERENCE_SIZE, resolve_imgsz

logger = logging.getLogger(__name__)


class FootfallCounter:
    def __init__(self, line_start: tuple[int, int], line_end: tuple[int, int],
                 detector_name: str = DEFAULT_DETECTOR, inference_size: str = DEFAULT_INFERENCE_SIZE) -> None:
        if sv is None:
            raise RuntimeError("Install ultralytics and supervision to use FootfallCounter")
        self.detector_name = detector_name
        self.inference_size = inference_size
        self._imgsz = resolve_imgsz(inference_size)
        self.model = load_model(detector_name)
        self.tracker = sv.ByteTrack()
        self._point = getattr(sv, "Point", lambda x, y: (x, y))
        self.line_zone = sv.LineZone(start=self._point(*line_start), end=self._point(*line_end))
        self._in_count = 0
        self._out_count = 0
        self.last_people_count = 0
        self.last_tracked_people_count = 0
        self.line_start = line_start
        self.line_end = line_end
        self._frame_count = 0

    def update_line(self, line_start: tuple[int, int], line_end: tuple[int, int]) -> None:
        """Recreate the line zone (e.g. when the source frame resolution changes)."""
        logger.info(
            "cormorant.counter.line_updated line_start=%s line_end=%s",
            line_start, line_end,
        )
        self.line_zone = sv.LineZone(start=self._point(*line_start), end=self._point(*line_end))
        self._in_count = 0
        self._out_count = 0
        self.line_start = line_start
        self.line_end = line_end

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
        if self.last_tracked_people_count > 0 and self._frame_count % 15 == 0:
            xyxy = detections.xyxy[0]
            cx = (xyxy[0] + xyxy[2]) / 2
            line_x = (self.line_start[0] + self.line_end[0]) / 2
            logger.info(
                "🚶 [%s] pessoa vista: posição x=%.0f | linha em x=%.0f | %s",
                self.detector_name, cx, line_x,
                "à direita da linha ➡️" if cx > line_x else "⬅️ à esquerda da linha",
            )
        triggered = self.line_zone.trigger(detections)
        entered, exited = self._triggered_detections(detections, triggered)
        if len(entered):
            logger.info("✅ ENTROU (IN) — total hoje: entradas=%s", self.line_zone.in_count)
        if len(exited):
            logger.info("✅ SAIU (OUT) — total hoje: saídas=%s", self.line_zone.out_count)
        return [self._event("IN", detection) for detection in entered] + [
            self._event("OUT", detection) for detection in exited
        ]

    def _triggered_detections(self, detections, triggered):
        if isinstance(triggered, tuple) and len(triggered) == 2:
            incoming, outgoing = triggered
            if hasattr(incoming, "__len__") and len(incoming) == len(detections):
                return self._detections_at(detections, incoming, is_mask=True), self._detections_at(detections, outgoing, is_mask=True)
        current_in, current_out = self.line_zone.in_count, self.line_zone.out_count
        new_in, new_out = max(0, current_in - self._in_count), max(0, current_out - self._out_count)
        self._in_count, self._out_count = current_in, current_out
        return self._detections_at(detections, range(new_in)), self._detections_at(detections, range(new_out))

    @staticmethod
    def _detections_at(detections, mask_or_indices, is_mask=False):
        indices = [index for index, selected in enumerate(mask_or_indices) if selected] if is_mask else mask_or_indices
        return [detections[index:index + 1] for index in indices]

    @staticmethod
    def _event(direction: str, detection) -> dict:
        return {"direction": direction, "tracker_id": int(detection.tracker_id[0]),
                "confidence": float(detection.confidence[0])}
